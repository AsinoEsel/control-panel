from .pwm import PWM
from controlpanel.shared.base.voltmeter import BaseVoltmeter
import asyncio


class Voltmeter(BaseVoltmeter, PWM):
    def __init__(self, artnet, name: str, pin: int, *, universe: int | None = None, noise_intensity=0.02) -> None:
        super().__init__(artnet, name, universe=universe, noise_intensity=noise_intensity)
        PWM.__init__(self, artnet, name, pin)

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
            