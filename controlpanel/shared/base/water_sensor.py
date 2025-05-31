from .sensor import Sensor


class BaseWaterSensor(Sensor):
    CORRECTION_FACTOR = 1.0

    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)
