from controlpanel.shared.base.pwm import BasePWM
import random

try:
    from time import ticks_ms
except ImportError:
    import time
    def ticks_ms(): return int(time.time() * 1000)


class BaseVoltmeter(BasePWM):
    def __init__(self, artnet, name: str, *, universe: int | None = None, noise_intensity: float = 0.02) -> None:
        super().__init__(artnet, name, universe=universe)
        # self.noise_intensity = noise_intensity
        # self._standard_duty = self._duty  # used to store the original duty value

    def parse_dmx_data(self, data: bytes):
        super().parse_dmx_data(data)
        self._standard_duty = self.duty

    def update(self):
        super().update()
        if not self.intensity_function:  # reset intensity to prevent needle from diverging too far
            self._duty = self._standard_duty
        self._duty += self.intensity_to_duty(random.uniform(-self.noise_intensity, self.noise_intensity))
