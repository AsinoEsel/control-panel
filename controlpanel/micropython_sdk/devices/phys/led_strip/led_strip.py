import neopixel
from machine import Pin
import asyncio
from ...base.led_strip import BaseLEDStrip


class LEDStrip(BaseLEDStrip):
    def __init__(self, artnet, name: str, pin: int, length: int, *, universe: int | None = None, animation=None) -> None:
        super().__init__(artnet, name, universe=universe, animation=animation)
        self.neopixels = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)

    def __len__(self):
        return len(self.neopixels)

    @property
    def buffer(self) -> bytearray:
        return self.neopixels.buf

    @buffer.setter
    def buffer(self, buf: bytearray):
        self.neopixels.buf = buf
        self.neopixels.write()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.neopixels.write()

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)