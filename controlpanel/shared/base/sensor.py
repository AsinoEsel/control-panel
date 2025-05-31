from .device import Device
try:
    from typing import Any
except ImportError:
    Any = object


class Sensor(Device):
    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
