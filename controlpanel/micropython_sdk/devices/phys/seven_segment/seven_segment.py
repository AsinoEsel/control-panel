from .max7219_8digit import Display
from machine import Pin, SoftSPI
from ...base.seven_segment import BaseSevenSegmentDisplay
import asyncio


class SevenSegmentDisplay(Display, BaseSevenSegmentDisplay):
    def __init__(self, artnet, name: str, spi: SoftSPI, gpio_chip_select: int, text: str = "", *, universe: int | None = None) -> None:
        super().__init__(spi, Pin(gpio_chip_select, Pin.OUT))
        BaseSevenSegmentDisplay.__init__(self, artnet, name, text, universe=universe)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, txt: str):
        self._text = txt
        self.write_to_buffer(txt)

    def update(self):
        self.display()

    async def run(self, updates_per_second: int):
        sleep_time = 1 / updates_per_second
        while True:
            self.update()
            await asyncio.sleep(sleep_time)
