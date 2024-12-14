import neopixel
from machine import Pin
import asyncio
from controlpanel.shared.base.led_strip import BaseLEDStrip


class LEDStrip(BaseLEDStrip):
    def __init__(self, artnet, name: str, pin: int, length: int, *, universe: int | None = None) -> None:
        super().__init__(artnet, name, universe=universe)
        self.neopixels = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)

    def __len__(self):
        return len(self.neopixels)

    def parse_dmx_data(self, data: bytes):
        assert len(data) == len(self.neopixels.buf) + self.DMX_STARTINDEX_PIXELS
        self.neopixels.buf[:] = data[self.DMX_STARTINDEX_PIXELS:]
        self.neopixels.write()

    # async def run(self, updates_per_second: int):
    #     sleep_time_ms = int(1000 / updates_per_second)
    #     while True:
    #         self.update()
    #         await asyncio.sleep_ms(sleep_time_ms)