import time
import random
import controlpanel.dmx
from controlpanel.scripts import ControlAPI, Event
from controlpanel.scripts.gui.window_manager import WindowManager
from controlpanel.scripts.gui.window_manager.window_manager_setup import *
from controlpanel.scripts.gui import widgets
import controlpanel.event_manager.dummy as devices


window_manager: WindowManager | None = ControlAPI.get_game("Window Manager")
if window_manager is None:
    raise ValueError()
intro: widgets.Desktop = window_manager.desktops.get("intro")


def write_prompt(text: str, color: tuple[int, int, int]):
    log: widgets.Log = intro.widget_manifest.get("Log")
    log.print_to_log(text, color)


class MyWindow(widgets.Window):
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            start_game()
        super().handle_event(event)


@ControlAPI.call_with_frequency(2.0)
def blink():
    intro: widgets.Desktop = window_manager.desktops.get("intro")
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
    # ControlAPI.fire_event("", "StartCountdown", 600)
    intro: widgets.Desktop = window_manager.desktops.get("intro")
    intro.close_window(intro.widget_manifest.get("WarningWindow"))
    # blink.stop()


@ControlAPI.callback(source_name="PowerSwitch")
def status_led_setter(event: Event):
    status_led: devices.DummyLEDStrip = ControlAPI.devices.get("StatusLED")
    color = (255, 0, 0) if event.value else (0, 255, 0)
    status_led.set_pixel(0, color)
    print(color)


@ControlAPI.callback(event_name="CommenceBlackout")
def blackout(event: Event):
    for fixture in ControlAPI.event_manager.fixture_dict.values():
        print(f"Blacking out {fixture.name}")
        fixture.blackout()


def set_up_desktops():
    intro = window_manager.create_new_desktop("intro", make_selected=True)

    intro.add_element(widgets.Terminal("Terminal", intro, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Log("Log", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP))
    intro.add_element(widgets.Image("Image", intro, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP,
                      image_path=os.path.join(os.path.dirname(__file__), "gui", "media", "robot36.png")))

    warning_window = MyWindow("WarningWindow", intro, "ALERT", RENDER_WIDTH//2, RENDER_HEIGHT//2, "The Control Panel will open at 6PM!")
    warning_window.add_element(widgets.Button("Continue", warning_window, 20, 50, 50, 10, "Continue", callback=start_game))
    intro.add_element(warning_window)


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
#
#
# @ControlAPI.call_with_frequency(1)
# def uv_random_strobe():
#     uv: devices.DummyPWM = ControlAPI.devices.get("UVStrobe")
#     if random.randint(0, 5) == 0:
#         uv.intensity = random.uniform(0.5, 1.0)
#         time.sleep(random.uniform(0.1, 0.4))
#         uv.intensity = 0.0



# def set_up_control_panel():
#     shrooms: devices.DummyLEDStrip = ControlAPI.devices.get("PilzLEDs")
#     shrooms.set_animation(2)


set_up_desktops()
set_up_dmx_fixtures()
# set_up_control_panel()
ControlAPI.fire_event("", "StartCountdown", 600)

