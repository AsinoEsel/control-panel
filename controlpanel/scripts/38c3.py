import enum
import time
import random
import controlpanel.dmx
from controlpanel.scripts import ControlAPI, Event
from controlpanel.scripts.gui.window_manager import WindowManager
from controlpanel.scripts.gui.window_manager.window_manager_setup import *
from controlpanel.scripts.gui import widgets
import controlpanel.event_manager.dummy as devices
from enum import IntEnum


class GameState(IntEnum):
    WAITING_ON_ANY_KEY_PRESS = enum.auto()
    WAITING_ON_BUTTON_PRESS = enum.auto()
    WAITING_ON_BATTERY_RECHARGE = enum.auto()


class CCCGame(WindowManager):
    def __init__(self):
        super().__init__("CCCGame")
        self.state_machine = GameState.WAITING_ON_ANY_KEY_PRESS
        self.battery_charge: float = 0.3
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

    def print_to_log(self, text: str, color: tuple[int, int, int]):
        print(f"printing to log {text}")
        self.desktops.get("intro").widget_manifest.get("TerminalLog").print_to_log(text, color)

    def button_press_success(self):
        BATTERIE_INDEX = 2
        ControlAPI.devices.get("ChronometerLampen").set_pixel(BATTERIE_INDEX, (255, 0, 0))
        self.print_to_log("BATTERY LEVELS LOW.", (255, 0, 0))
        self.print_to_log("RECHARGE BATTERY.", (255, 0, 0))
        self.print_to_log("PLEASE REFER TO 3.2.2 OF THE MANUAL.", (255, 0, 0))
        self.state_machine = GameState.WAITING_ON_BATTERY_RECHARGE

    def update(self) -> None:
        self.update_moving_head()
        match self.state_machine:
            case GameState.WAITING_ON_BUTTON_PRESS:
                if ControlAPI.devices.get("BigRedButton").state:
                    self.button_press_success()
            case GameState.WAITING_ON_BATTERY_RECHARGE:
                ...

        # self.battery_charge_level = max(0.0, self.battery_charge_level - self.dt * self.battery_charge_loss_per_second)
        # print(f"Current battery status: {self.battery_charge_level}")
        # print(f"Battery plugged in: {ControlAPI.devices.get("BatteryButtonLadestation").state}")

        super().update()


@ControlAPI.callback("BatteryButtonLadestation", "ButtonReleased")
def battery_pulled_out(event: Event):
    for i in range(1, 5):
        ControlAPI.devices.get(f"Voltmeter{i}").intensity = 0.0
        time.sleep(0.05)
    ControlAPI.devices.get("BatterySlotLadestation-LEDStrip").fill((0, 0, 0))
    ControlAPI.devices.get("BatterySlotBVG-LEDStrip").set_animation(1)


@ControlAPI.callback("BatteryButtonLadestation", "ButtonPressed")
def battery_plugged_in(event: Event):
    for i in range(1, 5):
        ControlAPI.devices.get(f"Voltmeter{i}").intensity = ccc_game.battery_charge
        time.sleep(0.1)


@ControlAPI.callback("BatteryButton", "ButtonReleased")
def battery_pulled_out_bvg(event: Event):
    ControlAPI.devices.get("BVGPanel").blackout()


@ControlAPI.callback("BatteryButton", "ButtonPressed")
def battery_plugged_in_bvg(event: Event):
    ControlAPI.devices.get("BVGPanel").send_dmx_data(b"\xff" * 4 * 16)
    ccc_game.battery_charge = 1.0
    ControlAPI.devices.get("Batterie").intensity = ccc_game.battery_charge
    ControlAPI.devices.get("BatterySlotLadestation-LEDStrip").fill((0, 0, 0))


class MyWindow(widgets.Window):
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            start_game()
        super().handle_event(event)


@ControlAPI.call_with_frequency(2.0)
def blink():
    ccc_game = ControlAPI.game_manager.get_game("CCCGame")
    if not ccc_game:
        return
    intro: widgets.Desktop = ccc_game.desktops.get("intro")
    if not intro:
        return
    warning_label: widgets.Window = intro.widget_manifest.get("WarningWindow")
    warning_label.color = (128, 0, 0, 255)
    warning_label.accent_color = (32, 0, 0, 255)
    warning_label.flag_as_needing_rerender()
    time.sleep(1.0)
    warning_label.color = (0, 128, 0, 255)
    warning_label.accent_color = (0, 32, 0, 255)
    warning_label.flag_as_needing_rerender()


def start_game():
    ControlAPI.fire_event("", "StartCountdown", 600)
    intro: widgets.Desktop = ccc_game.desktops.get("intro")
    intro.close_window(intro.widget_manifest.get("WarningWindow"))
    ControlAPI.dmx.devices.get("StarBar1").set_leds_to_color((255, 0, 0))
    ControlAPI.dmx.devices.get("StarBar2").set_leds_to_color((255, 0, 0))
    ControlAPI.dmx.devices.get("Spot1").animation = controlpanel.dmx.animations.red_strobe
    ControlAPI.dmx.devices.get("Spot2").animation = controlpanel.dmx.animations.red_strobe
    intro.widget_manifest.get("TerminalLog").print_to_log("DER COUNTDOWN LÄUFT", (255, 255, 255))
    ccc_game.state_machine = GameState.WAITING_ON_BUTTON_PRESS


# @ControlAPI.callback(source_name="PowerSwitch")
# def status_led_setter(event: Event):
#     status_led: devices.DummyLEDStrip = ControlAPI.devices.get("StatusLED")
#     color = (255, 0, 0) if event.value else (0, 255, 0)
#     status_led.set_pixel(0, color)
#     print(color)


# @ControlAPI.callback(event_name="CommenceBlackout")
# def blackout(event: Event):
#     for fixture in ControlAPI.event_manager.fixture_dict.values():
#         print(f"Blacking out {fixture.name}")
#         fixture.blackout()


def set_up_desktops():
    intro = ccc_game.create_new_desktop("intro", make_selected=True)
    intro.add_element(widgets.Terminal("Terminal", intro, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Log("Log", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Image("Image", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP,
                      image_path=os.path.join(os.path.dirname(__file__), "gui", "media", "robot36.png")))

    warning_window = MyWindow("WarningWindow", intro, "ALERT", RENDER_WIDTH//2, RENDER_HEIGHT//2, "The Control Panel will open at 6PM!")
    warning_window.add_element(widgets.Button("Continue", warning_window, 20, 50, 50, 10, "Continue", callback=start_game))
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
            # device._animation = (
            #     controlpanel.dmx.animations.starbar_strobe1
            # ) if device.name == "StarBar1" else (
            #     controlpanel.dmx.animations.starbar_strobe2
            # )


@ControlAPI.callback("BigRedButton", None, None)
def turn_on_motor(event: Event):
    chronometer: devices.DummyPWM = ControlAPI.devices.get("Chronometer")
    if event.value:
        chronometer.intensity = 1.0
    else:
        chronometer.intensity = 0.0


# @ControlAPI.call_with_frequency(1)
# def bvg_panel_on_the_fritz():
#     bvgpanel: devices.DummySipoShiftRegister = ControlAPI.devices.get("BVGPanel")
#     payload: bytes = bytes(0xFF if random.getrandbits(1) else 0x00 for _ in range(bvgpanel._number_of_bits))
#     bvgpanel.send_dmx_data(payload)


@ControlAPI.call_with_frequency(5)
def uv_random_strobe():
    uv: devices.DummyPWM = ControlAPI.devices.get("UVStrobe")
    if random.randint(0, 5) == 0:
        uv.intensity = random.uniform(0.5, 1.0)
        time.sleep(random.uniform(0.1, 0.4))
        uv.intensity = 0.0


@ControlAPI.callback(event_name="FullyInitiated")
def set_up_control_panel(event: Event):
    pass
    # shrooms: devices.DummyLEDStrip = ControlAPI.devices.get("PilzLEDs")
    # shrooms.set_animation(2)


ccc_game = CCCGame()
ControlAPI.add_game(ccc_game, make_current=True)
set_up_desktops()
intro: widgets.Desktop = ccc_game.desktops.get("intro")
set_up_dmx_fixtures()
