import controlpanel.dmx.devices
from controlpanel.scripts import ControlAPI, Event
from controlpanel.dmx.devices import MovingHead


# @ControlAPI.callback("ButtonRed", "ButtonPressed")
# @ControlAPI.callback("ButtonGreen", "ButtonPressed")
# @ControlAPI.callback("ButtonBlue", "ButtonPressed")
@ControlAPI.callback("ButtonPower", "ButtonPressed")
def callback_rgb(event: Event):
    red = "red" in event.name.lower()
    green = "green" in event.name.lower()
    blue = "blue" in event.name.lower()
    power = "power" in event.name.lower()
    print(red, green, blue, power)

    starbar: controlpanel.dmx.devices.VaritecColorsStarbar12 = ControlAPI.dmx.devices.get("StarBar1")
    r = 255 if red else 0
    g = 255 if green else 0
    b = 255 if blue else 0
    color = (r, g, b) if power else (0, 0, 0)
    starbar.set_leds_to_color(color)
    # calculate_color_of_moving_head(red, green, blue, power)


def calculate_color_of_moving_head(red, green, blue, power):
    moving_head: MovingHead = ControlAPI.dmx.devices.get("Laser")
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
