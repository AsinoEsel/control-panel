from controlpanel.scripts import ControlAPI, Event
from controlpanel.dmx.devices import MovingHead


# These variables keep track of the states of the switches
RED = False
GREEN = False
BLUE = False
POWER = False


@ControlAPI.callback("ButtonRed", "ButtonPressed", None)
@ControlAPI.callback("ButtonGreen", "ButtonPressed", None)
@ControlAPI.callback("ButtonBlue", "ButtonPressed", None)
@ControlAPI.callback("ButtonPower", "ButtonPressed", None)
def callback_rgb(event: Event):
    global RED, GREEN, BLUE, POWER

    if "red" in event.name.lower():
        RED = True
    if "green" in event.name.lower():
        GREEN = True
    if "blue" in event.name.lower():
        BLUE = True
    if "power" in event.name.lower():
        POWER = True

    calculate_color_of_moving_head()


def calculate_color_of_moving_head():
    moving_head: MovingHead = ControlAPI.dmx.devices.get("Laser")
    print(RED, GREEN, BLUE, POWER)
    if not POWER or (not RED and not GREEN and not BLUE):
        moving_head.intensity = 0
    else:
        moving_head.intensity = 1
        if not RED and not GREEN and BLUE:
            moving_head.color = 3
        elif not RED and GREEN and not BLUE:
            moving_head.color = 2
        elif not RED and GREEN and BLUE:
            moving_head.color = 6
        elif RED and not GREEN and not BLUE:
            moving_head.color = 1
        elif RED and not GREEN and BLUE:
            moving_head.color = 5
        elif RED and GREEN and not BLUE:
            moving_head.color = 4
        elif RED and GREEN and BLUE:
            moving_head.color = 0
