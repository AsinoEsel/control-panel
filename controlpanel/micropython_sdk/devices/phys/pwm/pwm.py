import machine
from ...base.pwm import BasePWM
import asyncio


class PWM(BasePWM):
    def __init__(self, artnet, name: str, pin: int, intensity: float = 1.0, *, universe: int | None = None, freq: int = 512, duty: int = 512, intensity_function=None) -> None:
        super().__init__(artnet, name, intensity, universe=universe, intensity_function=intensity_function)
        self.pin = machine.Pin(pin)
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(freq)
        self.pwm.duty(int(1023*intensity))

    @BasePWM.intensity.setter
    def intensity(self, value: float):
        self.duty = self.intensity_to_duty(value)
        self.pwm.duty(int(1023*value))

    async def run(self, updates_per_second: int):
        sleep_time = 1 / updates_per_second
        while True:
            self.update()
            await asyncio.sleep(sleep_time)
