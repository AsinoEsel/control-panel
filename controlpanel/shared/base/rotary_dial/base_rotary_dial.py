from ..sensor import Sensor


class BaseRotaryDial(Sensor):
    SUBKEY = 7

    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
