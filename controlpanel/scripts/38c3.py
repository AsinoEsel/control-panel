import time
import random
import controlpanel.dmx
from controlpanel.scripts import ControlAPI, Event
from controlpanel.scripts.gui.window_manager import WindowManager
from controlpanel.scripts.gui.window_manager.window_manager_setup import *
from controlpanel.scripts.gui import widgets
import controlpanel.event_manager.dummy as devices


PLUG_COLORS = (
    "orange",
    "blau",
    "rot",
    "gelb",
    "schwarz",
    "grün",
)


class CCCGame(WindowManager):
    BATTERY_DRAIN: float = 0.007  # drain per second
    BATTERY_CHARGE_SPEED: float = 0.1  # charge per second
    TEMPERATURE_RISE_SPEED: float = 0.01  # per second

    def __init__(self):
        super().__init__("CCCGame")
        self.battery_charge: float = 0.3
        self.plug_targets: list[int] = [0 for _ in range(4)]
        self.current_temp: float = 0.0
        self.reset()

    def shuffle_targets(self):
        self.plug_targets = random.sample(range(0, 6), 4)
        banana_plugs = ControlAPI.devices.get("BananaPlugs")
        current_connections = [x for x in banana_plugs.connections if x is not banana_plugs.NO_CONNECTION]
        while current_connections == banana_plugs.connections:
            self.plug_targets = random.sample(range(0, 6), 4)

    def reset(self):
        self.shuffle_targets()
        self.battery_charge = 0.3
        ControlAPI.devices.get("Batterie").intensity = self.battery_charge

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
            ControlAPI.devices.get("ButtonRed").state,
            ControlAPI.devices.get("ButtonGreen").state,
            ControlAPI.devices.get("ButtonBlue").state,
            ControlAPI.devices.get("ButtonPower").state,
        )

    def check_moving_head_alignment(self):
        if not ControlAPI.dmx:
            return
        from math import degrees, ceil, sqrt
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
        if not ControlAPI.devices.get("BatteryButton").state:
            multiplicator = 3.0 if ControlAPI.devices.get("PowerSwitch").state else 1.0
            self.battery_charge = max(0.0, self.battery_charge - self.BATTERY_DRAIN * self.dt * multiplicator)
        else:
            self.battery_charge = min(1.0, self.battery_charge + self.BATTERY_CHARGE_SPEED * self.dt)
            charge_points = int(ccc_game.battery_charge * 6)
            for i in range(charge_points):
                ControlAPI.devices.get("BVGPanel").set_bit(41 + i)
        ControlAPI.devices.get("Batterie").intensity = self.battery_charge
        if ControlAPI.devices.get("BatteryButtonLadestation").state:
            for i in range(1, 5):
                ControlAPI.devices.get(f"Voltmeter{i}").intensity = ccc_game.battery_charge

        if self.battery_charge < 0.4:
            ControlAPI.devices.get("ChronometerLampen").set_pixel(0, (255, 0, 0))
            # ccc_game.print_to_log(f"WARNING: BATTERY AT {ccc_game.battery_charge:.2%}!", (255, 255, 0))

    def print_to_log(self, text: str, color: tuple[int, int, int] = (0, 255, 0)):
        print(f"printing to log {text}")
        self.desktops.get("intro").widget_manifest.get("TerminalLog").print_to_log(text, color)

    def update(self) -> None:
        self.update_moving_head()
        self.check_moving_head_alignment()
        self.update_battery_charge()
        self.current_temp = min(1.0, self.current_temp + (self.TEMPERATURE_RISE_SPEED * self.dt))
        super().update()


@ControlAPI.callback(source_name="WaterFlowSensor")
def cooling_water(event: Event):
    COOLING_RATE = 0.005
    ccc_game.current_temp = max(0.0, ccc_game.current_temp - COOLING_RATE * event.value)


@ControlAPI.callback(source_name="TestHebel")
def test_hebel(event: Event):
    ControlAPI.fire_event(name="StartPlugPuzzle")


@ControlAPI.call_with_frequency(1.0)
def update_temperature():
    try:
        ControlAPI.devices.get("Temperature").intensity = ccc_game.current_temp
    except NameError:
        pass


@ControlAPI.callback(event_name="StartPlugPuzzle")
def start_plug_puzzle(event: Event):
    ccc_game.shuffle_targets()
    ccc_game.print_to_log("Lüftung verstopft. Überbrückung notwendig.", (255, 0, 0))
    ccc_game.print_to_log("Konsultieren Sie das Handbuch, Abschnitt 4.2", (255, 0, 0))
    ccc_game.print_to_log(f"Konfiguration:", (255, 255, 255))
    for i, target in enumerate(ccc_game.plug_targets):
        ccc_game.print_to_log(f"    Verbindung {i + 1}: {PLUG_COLORS[target]}")


@ControlAPI.callback(source_name="BananaPlugs", event_name="PlugConnected")
def plug_plugged(event: Event):
    banana_plugs = ControlAPI.devices.get("BananaPlugs")
    if banana_plugs.connections == ccc_game.plug_targets:
        ccc_game.print_to_log(f"Überbrückung der Lüftung erfolgreich abgeschlossen.")
        ControlAPI.fire_event(name="PlugPuzzleCompleted")


@ControlAPI.callback(event_name="PlugPuzzleCompleted")
def plug_puzzle_completed(event: Event):
    ...


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
    time.sleep(3.0)
    ccc_game.print_to_log("To enter your coordinates...", (0, 255, 0))


@ControlAPI.callback("BatteryButtonLadestation")
def battery_interaction_ladestation(event: Event):
    if event.value:  # PLUG IN
        for i in range(1, 5):
            ControlAPI.devices.get(f"Voltmeter{i}").intensity = ccc_game.battery_charge
            time.sleep(0.05)
        if ccc_game.battery_charge > 0.6:
            ControlAPI.devices.get("BatterySlotBVG-LEDStrip").set_animation(1)
            ControlAPI.devices.get("BatterySlotLadestation-LEDStrip").fill((255, 0, 0))
            time.sleep(3)
            ControlAPI.devices.get("BatterySlotLadestation-LEDStrip").fill((0, 0, 0))
    else:  # PLUG OUT
        for i in range(1, 5):
            ControlAPI.devices.get(f"Voltmeter{i}").intensity = 0.0
        if ccc_game.battery_charge <= 0.6:
            ControlAPI.devices.get("BatterySlotLadestation-LEDStrip").fill((0, 0, 0))
            ControlAPI.devices.get("BatterySlotBVG-LEDStrip").set_animation(1)


@ControlAPI.callback("BatteryButton")
def battery_interaction_bvgpanel(event: Event):
    if event.value:  # PLUG IN
        ControlAPI.devices.get("BatterySlotBVG-LEDStrip").fill((0, 0, 0))
    else:  # PLUG OUT
        ControlAPI.devices.get("BVGPanel").blackout()
        if ccc_game.battery_charge > 0.8:
            ControlAPI.devices.get("BatterySlotBVG-LEDStrip").fill((0, 0, 0))
            ControlAPI.devices.get("BatterySlotLadestation-LEDStrip").fill((0, 0, 255))
        else:
            ControlAPI.devices.get("BatterySlotBVG-LEDStrip").set_animation(1)


class PressAnyKeyWindow(widgets.Window):
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            ControlAPI.fire_event(self.name, "PressedAnyKey", None)
            self.close()
        super().handle_event(event)


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
        from controlpanel.scripts.gui.window_manager import FONT_PATH
        font = pg.font.Font(FONT_PATH, size=17)
        self.surface.fill(self.accent_color)
        for rect in self.charge_rects[:self.box_count]:
            if ccc_game.battery_charge > 0.8:
                color = (0, 255, 0)
            elif ccc_game.battery_charge > 0.4:
                color = (255, 200, 0)
            else:
                color = (200, 0, 0)
            pg.draw.rect(self.surface, color, rect)
        self.surface.blit(font.render("BATTERY CHARGE LEVEL", True, self.color), (5, 5))


@ControlAPI.call_with_frequency(2.0)
def blink():
    ccc_game: WindowManager | None = ControlAPI.game_manager.get_game("CCCGame")
    if not ccc_game:
        return
    intro: widgets.Desktop = ccc_game.desktops.get("intro")
    if not intro:
        return
    warning_label: widgets.Window = intro.widget_manifest.get("IntroWindow")
    warning_label.color = (128, 0, 0, 255)
    warning_label.accent_color = (32, 0, 0, 255)
    warning_label.flag_as_needing_rerender()
    time.sleep(1.0)
    warning_label.color = (0, 128, 0, 255)
    warning_label.accent_color = (0, 32, 0, 255)
    warning_label.flag_as_needing_rerender()


def set_up_desktops():
    intro = ccc_game.create_new_desktop("intro", make_selected=True)
    intro.add_element(widgets.Terminal("Terminal", intro, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Log("Log", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Image("Image", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP,
                      image_path=os.path.join(os.path.dirname(__file__), "gui", "media", "robot36.png")))

    warning_window = PressAnyKeyWindow("IntroWindow", intro, "ALERT", RENDER_WIDTH // 2, RENDER_HEIGHT // 2, "PRESS ANY BUTTON TO CONTINUE.")
    intro.add_element(BatteryChargeStatus(intro))
    intro.add_element(warning_window, make_active_element=True)


def set_up_dmx_fixtures():
    if not ControlAPI.dmx:
        return
    for device in ControlAPI.dmx.devices.values():
        if isinstance(device, controlpanel.dmx.RGBWLED):
            device._animation = controlpanel.dmx.animations.red_strobe
        if isinstance(device, controlpanel.dmx.VaritecColorsStarbar12):
            device.turn_off_lights()
            device.set_leds_to_color((0, 255, 0))


@ControlAPI.callback("BigRedButton", None, None)
def turn_on_motor(event: Event):
    chronometer: devices.DummyPWM = ControlAPI.devices.get("Chronometer")
    if event.value:
        chronometer.intensity = 1.0
    else:
        chronometer.intensity = 0.0


@ControlAPI.call_with_frequency(1)
def bvg_panel_glitch():
    bvgpanel: devices.DummySipoShiftRegister = ControlAPI.devices.get("BVGPanel")
    payload: bytes = bytes(0xFF if random.getrandbits(1) else 0x00 for _ in range(bvgpanel._number_of_bits))
    bvgpanel.send_dmx_data(payload)


@ControlAPI.call_with_frequency(5)
def uv_random_strobe():
    uv: devices.DummyPWM = ControlAPI.devices.get("UVStrobe")
    if random.randint(0, 5) == 0:
        uv.intensity = random.uniform(0.5, 1.0)
        time.sleep(random.uniform(0.1, 0.4))
        uv.intensity = 0.0


ccc_game = CCCGame()
ControlAPI.add_game(ccc_game, make_current=True)
set_up_desktops()
intro: widgets.Desktop = ccc_game.desktops.get("intro")
set_up_dmx_fixtures()
