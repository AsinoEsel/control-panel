"""
This module contains a list of all DMX devices that are PHYSICALLY connected to the USB to DMX adapter.
"""

from .devices import VaritecColorsStarbar12, MovingHead, RGBWLED


def red_strobe(t: float):
    return (255, 0, 0, 0) if t % 2 < 1 else (0, 0, 0, 0)


device_list = [
    MovingHead("Laser", 446, yaw_limit=(4.25, 6.55)),
    # VaritecColorsStarbar12("StarBar1", 31),
    VaritecColorsStarbar12("StarBar2", 460),
    # RGBWLED("Spot1", 15, animation=red_strobe),
    # RGBWLED("Spot2", 19, animation=red_strobe),
    # RGBWLED("Spot3", 23, animation=red_strobe),
    # RGBWLED("Spot4", 27, animation=red_strobe),
    # RGBWLED("Spot5", 135, animation=red_strobe),
    # RGBWLED("Spot6", 139, animation=red_strobe),
    # RGBWLED("Spot7", 143, animation=red_strobe),
    ]
