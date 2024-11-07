from ..fixture import Fixture
import struct

try:
    from time import ticks_ms
except ImportError:
    import time
    def ticks_ms(): return int(time.time() * 1000)


class BasePWM(Fixture):
    def __init__(self, artnet, name: str, intensity: float = 1.0, *, universe: int | None = None, intensity_function=None) -> None:
        super().__init__(artnet, name, universe=universe)
        self._duty = int(intensity*1023)
        self.intensity_function = intensity_function

    @property
    def duty(self) -> int:
        return self._duty

    @duty.setter
    def duty(self, value):
        self._duty = value

    @staticmethod
    def intensity_to_duty(intensity: float) -> int:
        return min(1023, max(int(intensity*1023), 0))

    @property
    def intensity(self) -> float:
        return self.duty / 1023

    @intensity.setter
    def intensity(self, value: float):
        self.duty = self.intensity_to_duty(value)

    def get_dmx_data(self) -> bytearray:
        return bytearray(struct.pack('H', self.duty & 0b1111111111))

    def parse_dmx_data(self, data: bytes):
        self._duty = struct.unpack("H", data)[0]

    def update(self):
        if self.intensity_function:
            self.intensity = self.intensity_function(ticks_ms())
