from ..sensor import Sensor
import struct
from controlpanel.shared.subkey_manifest import SubKey


class BaseWaterSensor(Sensor):
    SUBKEY = SubKey.Double
    CORRECTION_FACTOR = 1.0

    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)
