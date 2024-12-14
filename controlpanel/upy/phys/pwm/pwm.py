import struct

import machine
from controlpanel.shared.base.pwm import BasePWM
import asyncio


class PWM(BasePWM):
    def __init__(self, artnet, name: str, pin: int, intensity: float = 1.0, *, universe: int | None = None, freq: int = 512) -> None:
        super().__init__(artnet, name, universe=universe)
        self.pin = machine.Pin(pin)
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(freq)
        self.pwm.duty(int(1023*intensity))

    def parse_dmx_data(self, data: bytes):
        self.pwm.duty(data[0] * 4)

    # async def run(self, updates_per_second: int):
    #     sleep_time = 1 / updates_per_second
    #     while True:
    #         self.update()
    #         await asyncio.sleep(sleep_time)
