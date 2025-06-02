from .max7219 import SevenSegment
from controlpanel.shared.base.seven_segment import BaseSevenSegmentDisplay
from controlpanel.upy.phys import FixtureMixin


class SevenSegmentDisplay(SevenSegment, BaseSevenSegmentDisplay, FixtureMixin):
    def __init__(self, artnet, name: str, digits: int, gpio_chip_select: int, *, universe: int | None = None) -> None:
        super().__init__(digits, cs=gpio_chip_select, reverse=True)
        BaseSevenSegmentDisplay.__init__(self, artnet, name, universe=universe)

    def parse_dmx_data(self, data: bytes) -> None:
        self.text(data.decode("ascii"))

    # async def run(self, updates_per_second: int):
    #     sleep_time = 1 / updates_per_second
    #     while True:
    #         self.update()
    #         await asyncio.sleep(sleep_time)
