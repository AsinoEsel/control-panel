from ..sensor import Sensor
import struct


class BaseWaterFlowSensor(Sensor):
    SUBKEY = 4
    CORRECTION_FACTOR = 1.0

    def __init__(self, artnet, name: str, *, callback=None) -> None:
        super().__init__(artnet, name, callback=callback)
        self.flow_counter = 0

    def update(self):
        if self.flow_counter > 0:
            self.callback(self.flow_counter)
            # self.flow_counter = 0

    def get_payload(self) -> bytes:
        print(self.flow_counter)
        return struct.pack("<d", self.flow_counter * self.CORRECTION_FACTOR)
    