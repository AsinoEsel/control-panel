from .max7219 import SevenSegment
from machine import Pin, SoftSPI
from ...base.seven_segment import BaseSevenSegmentDisplay
import asyncio


class SevenSegmentDisplay(SevenSegment, BaseSevenSegmentDisplay):
    def __init__(self, artnet, name: str, digits: int, gpio_chip_select: int, text: str = "", *, universe: int | None = None) -> None:
        super().__init__(digits, cs=gpio_chip_select, reverse=True)
        BaseSevenSegmentDisplay.__init__(self, artnet, name, text, universe=universe)

    async def run(self, updates_per_second: int):
        sleep_time = 1 / updates_per_second
        while True:
            self.update()
            await asyncio.sleep(sleep_time)
