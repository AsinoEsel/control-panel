import time
import random
import controlpanel.dmx
from controlpanel.scripts import ControlAPI, Event
from gui.window_manager import WindowManager
from gui.window_manager.window_manager_setup import *
from gui import widgets
import controlpanel.event_manager.dummy as devices
from datetime import datetime
from fourteensegment import Display, rgb_to_b16

UNIVERSE = 14
DISPLAY_COUNT = 3

PLUG_COLORS = (
    "orange",
    "blau",
    "rot",
    "gelb",
    "schwarz",
    "grün",
)

ANTENNA_COLORS = (
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (255, 255, 255),
)


class CCCGame(WindowManager):
    BATTERY_DRAIN: float = 0.003  # drain per second
    BATTERY_CHARGE_SPEED: float = 0.1  # charge per second
    BATTERY_WARNING_THRESHOLD: float = 0.25
    TEMPERATURE_RISE_SPEED: float = 0.002  # per second
    TEMPERATURE_WARNING_THRESHOLD: float = 0.8

    def __init__(self):
        super().__init__("CCCGame")
        self.antennas_aligned: int = 0
        self.antenna_receiver_color: tuple[int, int, int] = random.choice(ANTENNA_COLORS)
        self.battery_charge: float = 0.3
        self.plug_targets: list[int] = [0 for _ in range(4)]
        self.current_temp: float = 0.0
        self.antennas_completed: int = 0
        self.ready_for_highscore: int = 0
        self.plug_puzzle_started: int = 0
        self.plug_puzzle_completed: int = 0
        self.entered_numbers: list[int] = []
        self.start_time = datetime.now()

        self.display = Display(DISPLAY_COUNT)
        self.display.clear()

        self.reset()

    def shuffle_targets(self):
        self.plug_targets = random.sample(range(0, 6), 4)
        banana_plugs = ControlAPI.get_device("BananaPlugs")
        current_connections = [x for x in banana_plugs.connections if x is not banana_plugs.NO_CONNECTION]
        while current_connections == banana_plugs.connections:
            self.plug_targets = random.sample(range(0, 6), 4)

    def update_fourteen_segment(self):

        now = datetime.now()
        diff = (now - self.start_time).total_seconds()
        if diff < 240:
            color = rgb_to_b16(0, 255, 0)
        elif diff < 600:
            color = rgb_to_b16(255, 255, 0)
        else:
            color = rgb_to_b16(255, 0, 0)

        self.display.send_dmx(UNIVERSE, 0, self.display.text_to_data(f" {str(min(99, int(diff//60))).zfill(2)}:{str(int(diff%60)).zfill(2)} ", color))


    def reset(self):
        print("Resetting game...")
        self.plug_puzzle_started: int = 0
        self.antennas_aligned = 0
        self.shuffle_targets()
        self.battery_charge = 0.3
        self.antennas_completed = 0
        self.ready_for_highscore = 0
        self.plug_puzzle_completed = 0
        self.start_time = datetime.now()

        ControlAPI.get_device("Batterie").intensity = self.battery_charge

    def handle_events(self, events: list[pg.event.Event]) -> None:
        for event in events:
            if ControlAPI.dmx and ControlAPI.dmx.devices.get("Laser"):
                laser = ControlAPI.dmx.devices.get("Laser")
                mods = pg.key.get_mods()
                if event.type == pg.JOYBUTTONDOWN and event.button == 0:
                    laser.strobe = True
                elif event.type == pg.JOYBUTTONUP and event.button == 0:
                    laser.strobe = False
                elif event.type == pg.JOYBUTTONDOWN and event.button == 2:
                    laser.gobo1 += 1
                elif event.type == pg.JOYBUTTONDOWN and event.button == 3:
                    laser.gobo2 += 1
                elif event.type == pg.JOYBUTTONDOWN and event.button == 1:
                    laser.gobo1 = 0
                    laser.gobo2 = 0

                if event.type == pg.KEYDOWN and event.key == pg.K_p:
                    laser.prism = not laser.prism
                elif event.type == pg.KEYDOWN and event.key == pg.K_c:
                    laser.color += 1
                elif event.type == pg.KEYDOWN and event.key == pg.K_g:
                    if mods & pg.KMOD_CTRL:
                        laser.gobo1 += 1
                    else:
                        laser.gobo1 -= 1
                elif event.type == pg.KEYDOWN and event.key == pg.K_h:
                    if mods & pg.KMOD_CTRL:
                        laser.gobo2 += 1
                    else:
                        laser.gobo2 -= 1
        super().handle_events(events)

    @staticmethod
    def calculate_color_of_moving_head(red, green, blue, power):
        if not ControlAPI.dmx:
            return
        moving_head: controlpanel.dmx.devices.MovingHead = ControlAPI.dmx.devices.get("Laser")
        if not power or (not red and not green and not blue):
            moving_head.intensity = 0
        else:
            moving_head.intensity = 1
            if not red and not green and blue:
                moving_head.color = 3
            elif not red and green and not blue:
                moving_head.color = 2
            elif not red and green and blue:
                moving_head.color = 6
            elif red and not green and not blue:
                moving_head.color = 1
            elif red and not green and blue:
                moving_head.color = 5
            elif red and green and not blue:
                moving_head.color = 4
            elif red and green and blue:
                moving_head.color = 0

    def update_moving_head(self):
        from math import radians
        from controlpanel.scripts import ControlAPI
        max_speed = radians(45)
        max_distance = max_speed * self.dt

        for joystick in self._joysticks.values():
            axes: list[float] = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
            laser: controlpanel.dmx.devices.MovingHead = ControlAPI.dmx.devices.get("Laser")
            laser.yaw += axes[0] * abs(axes[0]) * max_distance
            laser.pitch -= axes[1] * abs(axes[1]) * max_distance
            laser.gobo2_rotation = axes[2]
            laser.focus = (axes[3] + 1) / 2
            hat = joystick.get_hat(0)

        self.calculate_color_of_moving_head(
            ControlAPI.get_device("ButtonRed").state,
            ControlAPI.get_device("ButtonGreen").state,
            ControlAPI.get_device("ButtonBlue").state,
            ControlAPI.get_device("ButtonPower").state,
        )

    def check_moving_head_alignment(self):
        if not ControlAPI.dmx:
            return
        from math import degrees, ceil
        target_yaw = 5.17
        target_pitch = -1.44
        target_vector = pg.Vector3.from_spherical((1.0, degrees(target_pitch), degrees(target_yaw)))
        moving_head: controlpanel.dmx.devices.MovingHead = ControlAPI.dmx.devices.get("Laser")
        moving_head_vector = pg.Vector3.from_spherical((1.0, degrees(moving_head.pitch), degrees(moving_head.yaw)))
        angle = target_vector.angle_to(moving_head_vector)
        starbar1: controlpanel.dmx.devices.VaritecColorsStarbar12 = ControlAPI.dmx.devices.get("StarBar1")
        starbar2: controlpanel.dmx.devices.VaritecColorsStarbar12 = ControlAPI.dmx.devices.get("StarBar2")
        rating = 1.0 - min(1.0, max(0.0, angle/50))
        adjusted_rating = rating ** 2
        stars = ceil(starbar1.LED_COUNT * adjusted_rating)
        starbar1.strobe = 100 if stars == 12 else 0  # perfect score!
        starbar2.strobe = 100 if stars == 12 else 0
        for i in range(starbar1.LED_COUNT):
            if i < stars:
                starbar1.lights[i] = 255
                starbar2.lights[i] = 255
            else:
                starbar1.lights[i] = 0
                starbar2.lights[i] = 0

    def update_battery_charge(self):
        old_charge_level = self.battery_charge

        if not ControlAPI.get_device("BatteryButton").state:
            multiplicator = 3.0 if ControlAPI.get_device("PowerSwitch").state else 1.0
            self.battery_charge = max(0.0, self.battery_charge - self.BATTERY_DRAIN * self.dt * multiplicator)
        else:
            self.battery_charge = min(1.0, self.battery_charge + self.BATTERY_CHARGE_SPEED * self.dt)
            charge_points = int(ccc_game.battery_charge * 6)
            for i in range(charge_points):
                ControlAPI.get_device("BVGPanel").set_bit(41 + i)
        ControlAPI.get_device("Batterie").intensity = self.battery_charge
        if ControlAPI.get_device("BatteryButtonLadestation").state:
            for i in range(1, 5):
                ControlAPI.get_device(f"Voltmeter{i}").intensity = ccc_game.battery_charge

        if self.battery_charge < 0.4:
            ControlAPI.get_device("ChronometerLampen").set_pixel(2, (255, 0, 0))
            # ccc_game.print_to_log(f"WARNING: BATTERY AT {ccc_game.battery_charge:.2%}!", (255, 255, 0))

        if self.battery_charge < self.BATTERY_WARNING_THRESHOLD < old_charge_level:
            ccc_game.add_popup("WARNING. ENERGY CELL STATUS CRITICAL.", f"The battery charge is at {self.BATTERY_WARNING_THRESHOLD:.0%}."
                               "Please take the battery out of the recepticle and insert it into the charging station.")
            self.print_to_log(f"WARNING. ENERGY CELL STATUS CRITICAL.", color=(255, 0, 0))
            self.print_to_log(f"PLEASE CHARGE BATTERY.", color=(255, 0, 0))
        if self.battery_charge > self.BATTERY_WARNING_THRESHOLD and ControlAPI.get_device("BatteryButtonLadestation").state:
            popup = ccc_game.desktop.widget_manifest.get("WARNING. ENERGY CELL STATUS CRITICAL.")
            if popup:
                popup.close()
                self.print_to_log(f"Energy cell successfully recharged to {self.battery_charge:.0%}.")
                ControlAPI.get_device("ChronometerLampen").set_pixel(2, (0, 0, 0))

    def print_to_log(self, text: str, color: tuple[int, int, int] = (0, 255, 0)):
        self.desktops.get("intro").widget_manifest.get("TerminalLog").print_to_log(text, color, True)

    def update_temperature(self):
        old_temp = self.current_temp
        self.current_temp = min(1.0, self.current_temp + (self.TEMPERATURE_RISE_SPEED * self.dt))
        if self.current_temp > self.TEMPERATURE_WARNING_THRESHOLD > old_temp:
            ccc_game.add_popup("WARNING. HIGH TEMPERATURE.", f"TEMPERATURE AT {self.TEMPERATURE_WARNING_THRESHOLD:.0%}."
                               "Please refill cooling water.")
            self.print_to_log(f"WARNING: TEMPERATURE AT {self.TEMPERATURE_WARNING_THRESHOLD:.0%}.")
            self.print_to_log(f"Please refill cooling water.")
        if self.current_temp < self.TEMPERATURE_WARNING_THRESHOLD:
            popup = ccc_game.desktop.widget_manifest.get("WARNING. HIGH TEMPERATURE.")
            if popup:
                popup.close()
                self.print_to_log(f"Temperature sucessfully stabilized.")

    def update_antenna(self):
        if not ControlAPI.dmx:
            return
        sender_starbar: controlpanel.dmx.devices.VaritecColorsStarbar12 = ControlAPI.dmx.devices.get("StarBar1")
        receiver_starbar: controlpanel.dmx.devices.VaritecColorsStarbar12 = ControlAPI.dmx.devices.get("StarBar2")
        r = 255 if ControlAPI.get_device("ButtonRed").state else 0
        g = 255 if ControlAPI.get_device("ButtonGreen").state else 0
        b = 255 if ControlAPI.get_device("ButtonBlue").state else 0
        sender_color = (r, g, b) if ControlAPI.get_device("ButtonPower").state else (0, 0, 0)
        sender_starbar.set_leds_to_color(sender_color)
        if sender_color == self.antenna_receiver_color:
            self.antennas_aligned += 1
            ControlAPI.fire_event(name="AntennaAligned", value=self.antennas_aligned)
            while self.antenna_receiver_color == sender_color:
                self.antenna_receiver_color = random.choice(ANTENNA_COLORS)
            receiver_starbar.set_leds_to_color(self.antenna_receiver_color)
            receiver_starbar.turn_off_lights()
        sender_starbar.lights = [255 for _ in range(self.antennas_aligned)] + [0 for _ in range(sender_starbar.LED_COUNT - self.antennas_aligned)]

    def update(self) -> None:
        # self.update_moving_head()
        # self.check_moving_head_alignment()
        if not self.ready_for_highscore:
            self.update_battery_charge()
            self.update_temperature()
            self.update_antenna()
            self.update_fourteen_segment()
        super().update()

    def add_any_key_popup(self, title: str, text: str):
        if self.desktop.widget_manifest.get(title) is None:
            self.desktop.add_element(PressAnyKeyWindow(title, self.desktop, title, RENDER_WIDTH // 2, RENDER_HEIGHT // 2, text), make_active_element=True)

    def add_popup(self, title: str, text: str):
        if self.desktop.widget_manifest.get(title) is None:
            self.desktop.add_element(CriticalWarningWindow(title, self.desktop, title, RENDER_WIDTH // 2, RENDER_HEIGHT // 2, text), make_active_element=True)


@ControlAPI.callback(source_name="WaterFlowSensor")
def cooling_water(event: Event):
    COOLING_RATE = 0.005
    ccc_game.current_temp = max(0.0, ccc_game.current_temp - COOLING_RATE * event.value)


@ControlAPI.callback(event_name="AntennaAligned")
def antenna_aligned(event: Event):
    if event.value < 12:
        ControlAPI.dmx.devices.get("StarBar2").strobe = 100
        time.sleep(1)
        ControlAPI.dmx.devices.get("StarBar2").strobe = 0
    else:
        ccc_game.add_any_key_popup("CALIBRATION COMPLETE", "The communication array has been calibrated.")
        ccc_game.print_to_log("Calibration successful.")



@ControlAPI.call_with_frequency(1.0)
def update_temperature():
    try:
        ControlAPI.get_device("Temperature").intensity = ccc_game.current_temp
        if ccc_game.current_temp > ccc_game.TEMPERATURE_WARNING_THRESHOLD:
            ControlAPI.get_device("WarnLED").intensity = 0.0 if ControlAPI.get_device("WarnLED").intensity else 1.0
        else:
            ControlAPI.get_device("WarnLED").intensity = 0.0
    except NameError:
        pass


@ControlAPI.callback(event_name="StartPlugPuzzle")
def start_plug_puzzle(event: Event):
    if ccc_game.plug_puzzle_started:
        return
    ccc_game.shuffle_targets()
    ccc_game.print_to_log("Lüftung verstopft. Überbrückung notwendig.", (255, 0, 0))
    ccc_game.print_to_log("Konsultieren Sie das Handbuch, Abschnitt 4.1", (255, 0, 0))
    ccc_game.print_to_log(f"Konfiguration:", (255, 255, 255))
    ccc_game.plug_puzzle_started = 1
    for i, target in enumerate(ccc_game.plug_targets):
        ccc_game.print_to_log(f"    Verbindung {i + 1}: {PLUG_COLORS[target]}")


@ControlAPI.callback(source_name="BananaPlugs", event_name="PlugConnected")
def plug_plugged(event: Event):
    banana_plugs = ControlAPI.get_device("BananaPlugs")
    if banana_plugs.connections == ccc_game.plug_targets:
        ControlAPI.fire_event(name="PlugPuzzleCompleted")


@ControlAPI.callback(event_name="PlugPuzzleCompleted")
def plug_puzzle_completed(event: Event):
    ccc_game.print_to_log("Rerouting ventilation...", (255, 255, 0))
    time.sleep(3.0)
    ccc_game.print_to_log("Reroute Successful!", (0, 255, 0))
    ccc_game.plug_puzzle_completed = 1

@ControlAPI.callback("IntroWindow", "PressedAnyKey", fire_once=True)
def any_key_pressed(event: Event):
    # ccc_game.print_to_log("You may now enter your destination coordinates.", (255, 0, 0))
    # time.sleep(1.0)
    # ccc_game.print_to_log("Please note that failure to commence travel within a window of...", (255, 255, 0))
    # time.sleep(3.0)
    # ccc_game.print_to_log("Ten.", (255, 0, 0))
    # time.sleep(1.0)
    # ccc_game.print_to_log("minutes will result in an unsatisfactory mark on your official record.", (255, 0, 0))
    # time.sleep(3.0)
    # ccc_game.print_to_log("Followed by a collapse of your local space-time continuum.", (255, 0, 0))
    # time.sleep(3.0)
    # ccc_game.print_to_log("Starting...", (255, 255, 0))
    # time.sleep(2.0)
    # ccc_game.print_to_log("Now.", (255, 0, 0))
    if ControlAPI.dmx:
        ControlAPI.dmx.devices.get("StarBar1").turn_on_lights()
        ControlAPI.dmx.devices.get("StarBar2").turn_on_lights()
        ControlAPI.dmx.devices.get("StarBar1").set_leds_to_color((255, 0, 0))
        ControlAPI.dmx.devices.get("StarBar2").set_leds_to_color((255, 0, 0))
        ControlAPI.dmx.devices.get("Spot1").animation = controlpanel.dmx.animations.red_strobe
        ControlAPI.dmx.devices.get("Spot2").animation = controlpanel.dmx.animations.red_strobe
    ControlAPI.fire_event("", "StartCountdown", 600)


@ControlAPI.callback("BatteryButtonLadestation")
def battery_interaction_ladestation(event: Event):
    if event.value:  # PLUG IN
        for i in range(1, 5):
            ControlAPI.get_device(f"Voltmeter{i}").intensity = ccc_game.battery_charge
            time.sleep(0.05)
        if ccc_game.battery_charge > 0.6:
            ControlAPI.get_device("BatterySlotBVG-LEDStrip").set_animation(1)
            ControlAPI.get_device("BatterySlotLadestation-LEDStrip").fill((255, 0, 0))
            time.sleep(3)
            ControlAPI.get_device("BatterySlotLadestation-LEDStrip").fill((0, 0, 0))
    else:  # PLUG OUT
        for i in range(1, 5):
            ControlAPI.get_device(f"Voltmeter{i}").intensity = 0.0
        if ccc_game.battery_charge <= 0.6:
            ControlAPI.get_device("BatterySlotLadestation-LEDStrip").fill((0, 0, 0))
            ControlAPI.get_device("BatterySlotBVG-LEDStrip").set_animation(1)


@ControlAPI.callback("BatteryButton")
def battery_interaction_bvgpanel(event: Event):
    if event.value:  # PLUG IN
        ControlAPI.get_device("BatterySlotBVG-LEDStrip").fill((0, 0, 0))
    else:  # PLUG OUT
        ControlAPI.get_device("BVGPanel").blackout()
        if ccc_game.battery_charge > 0.8:
            ControlAPI.get_device("BatterySlotBVG-LEDStrip").fill((0, 0, 0))
            ControlAPI.get_device("BatterySlotLadestation-LEDStrip").fill((0, 0, 255))
        else:
            ControlAPI.get_device("BatterySlotBVG-LEDStrip").set_animation(1)


class PressAnyKeyWindow(widgets.Window):
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            ControlAPI.fire_event(self.name, "PressedAnyKey", None)
            self.close()
        super().handle_event(event)


class CriticalWarningWindow(widgets.Window):
    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

    def update(self, tick: int, dt: float, joysticks: dict[int: pg.joystick.JoystickType]):
        if tick % 13 == 0:
            self.color = (255, 0, 0)
            self.accent_color = (64, 0, 0)
            self.flag_as_needing_rerender()
        if tick % 29 == 0:
            self.color = (0, 255, 0)
            self.accent_color = (0, 64, 0)
            self.flag_as_needing_rerender()


class BatteryChargeStatus(widgets.Widget):
    def __init__(self, parent):
        super().__init__("BatteryChargeStatus", parent, RENDER_WIDTH*0.75, 10, RENDER_WIDTH*0.2, 50)
        self.charge_rects = [pg.Rect(i * (RENDER_WIDTH*0.2)/5, 20, (RENDER_WIDTH*0.2)/5, 35) for i in range(5)]
        self.box_count: int = 5

    def update(self, tick: int, dt: float, joysticks: dict[int: pg.joystick.JoystickType]):
        new_box_count = round(ccc_game.battery_charge * 5)
        if self.box_count == new_box_count:
            return
        self.box_count = new_box_count
        self.flag_as_needing_rerender()

    def render_body(self):
        from gui.window_manager import FONT_PATH
        from gui.media import load_file_stream
        font = pg.font.Font(load_file_stream(FONT_PATH), size=17)
        battery_inserted = ControlAPI.get_device("BatteryButtonLadestation").state
        battery_inserted_charger = ControlAPI.get_device("BatteryButton").state
        self.surface.fill(self.accent_color)
        for rect in self.charge_rects[:self.box_count]:
            if ccc_game.battery_charge > 0.8:
                color = (0, 255, 0) if battery_inserted or battery_inserted_charger else (64, 64, 64)
            elif ccc_game.battery_charge > 0.4:
                color = (255, 200, 0) if battery_inserted or battery_inserted_charger else (32, 32, 32)
            else:
                color = (200, 0, 0) if battery_inserted or battery_inserted_charger else (6, 6, 6)
            pg.draw.rect(self.surface, color, rect)
        if not battery_inserted:
            if battery_inserted_charger:
                text = "BATTERY IN CHARGING PORT"
            else:
                text = "BATTERY DISCONNECTED"
            text_color = (255, 255, 255)
        elif ControlAPI.get_device("ButtonPower").state:
            text = "ANTENNA ONLINE. HIGH DRAIN."
            text_color = (255, 0, 0)
        else:
            text = "BATTERY CHARGE LEVEL"
            text_color = self.color
        self.surface.blit(font.render(text, True, text_color), (5, 5))


def set_up_desktops():
    intro = ccc_game.create_new_desktop("intro", make_selected=True)
    intro.add_element(widgets.Terminal("Terminal", intro, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Log("Log", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Image("Image", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP,
                      image_path="robot36.png"))

    warning_window = PressAnyKeyWindow("IntroWindow", intro, "ALERT", RENDER_WIDTH // 2, RENDER_HEIGHT // 2, "PRESS ANY BUTTON TO CONTINUE.")
    intro.add_element(BatteryChargeStatus(intro))
    intro.add_element(warning_window, make_active_element=True)


def set_up_dmx_fixtures():
    if not ControlAPI.dmx:
        return
    for device in ControlAPI.dmx.devices.values():
        if isinstance(device, controlpanel.dmx.RGBWLED):
            device._animation = controlpanel.dmx.animations.red_strobe


@ControlAPI.call_with_frequency(1)
def bvg_panel_glitch():
    if ControlAPI.get_device("BatteryButton").state:  # dont glitch if charging
        return
    bvgpanel: devices.DummySipoShiftRegister = ControlAPI.get_device("BVGPanel")
    payload: bytes = bytes(0xFF if random.getrandbits(1) else 0x00 for _ in range(bvgpanel._number_of_bits))
    bvgpanel.send_dmx_data(payload)


@ControlAPI.call_with_frequency(5)
def uv_random_strobe():
    uv: devices.DummyPWM = ControlAPI.get_device("UVStrobe")
    if random.randint(0, 5) == 0:
        uv.intensity = random.uniform(0.5, 1.0)
        time.sleep(random.uniform(0.1, 0.4))
        uv.intensity = 0.0


@ControlAPI.callback(source_name="AuthorizationKeyBVG")
@ControlAPI.callback(source_name="AuthorizationKeyCharge")
def zuendung(event: Event):
    # Both Keys are pressed. We can Check if all conditions are met to start time traveling
    if ControlAPI.get_device("AuthorizationKeyBVG") and ControlAPI.get_device("AuthorizationKeyCharge"):
        ControlAPI.get_device("Chronometer").intensity = 1.0
    else:
        return



    # One needs to solve the Plug Puzzle Game
    if not ccc_game.plug_puzzle_completed:
        time.sleep(2.0)
        ControlAPI.get_device("Chronometer").intensity = 0.0
        ControlAPI.fire_event(name="StartPlugPuzzle")
        return

    # The Antennas needs to be configured:
    if ccc_game.antennas_aligned < 12:
        time.sleep(2.0)
        ControlAPI.get_device("Chronometer").intensity = 0.0
        text = "The communication antennas are not configured." if ccc_game.antennas_aligned == 0 else "The communication antennas are not fully configured"
        text += "Ensure that both antennas are communicating on the same frequency bands before proceeding."
        ccc_game.add_any_key_popup("MISALIGNMENT IN ANTENNA ARRAY.", text)
        ccc_game.print_to_log(f"Configure antennas, currently {ccc_game.antennas_aligned} antennas ready")
    else:
        text = "Congratulation, you configured the communication antennas! You are ready to launch the time travel"
        ccc_game.add_any_key_popup("READY TO START", text)
        ccc_game.print_to_log(f"Ready to Start Time Traveling")
        ccc_game.antennas_completed = 1

@ControlAPI.callback(source_name="BigRedButton")
def the_end(event: Event):
    # The game is finished, congratulation to the user
    if ccc_game.antennas_completed and ccc_game.plug_puzzle_completed:
        text = f"You are flying through the time line, towards a the year {random.randint(2026,2999)} where everyone lives in peace and harmony. Please enter your name to store in the leader board"
        # TODO find a proper random day and year, browse through wikipedia and report some events happening this year.
        ccc_game.add_any_key_popup("FINISHED TIMETRAVEL", text)
        ccc_game.ready_for_highscore = 1

@ControlAPI.callback("TerminalInputBox", "TextInput")
def get_highscore(event: Event):
    # Get the high score name and add it to a txt file
    if ccc_game.antennas_completed and ccc_game.ready_for_highscore:
        name = str(event.value)
        now = datetime.now()
        took_time = (now - ccc_game.start_time).total_seconds()

        current_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        with open("/home/roboter/Desktop/winners.txt", "a") as f:
            f.write(current_time + ": " + name + f" |{str(int(took_time//60))}:{str(int(took_time%60))}\n")
        with open("/home/roboter/Desktop/winners.txt", "r") as f:
            names = f.readlines()
        # TODO Sort Leaderboard by taken time!
        ccc_game.add_any_key_popup("Last Creatures Solved:", "\n".join(names[-10:]))
        ccc_game.reset()

ccc_game = CCCGame()
ControlAPI.add_game(ccc_game, make_current=True)
set_up_desktops()
intro: widgets.Desktop = ccc_game.desktops.get("intro")
set_up_dmx_fixtures()
