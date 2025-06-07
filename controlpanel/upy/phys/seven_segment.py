from controlpanel.shared.base.seven_segment import BaseSevenSegmentDisplay
from .fixture import Fixture
from controlpanel.upy.libs.seven_segment import SevenSegment
from controlpanel.upy.artnet import ArtNet
try:
    from typing import Literal
except ImportError:
    Literal = object()


class SevenSegmentDisplay(BaseSevenSegmentDisplay, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 digits: int,
                 pin_chip_select: int,
                 hardware_spi: Literal[1, 2],
                 *,
                 universe: int | None = None
                 ) -> None:
        Fixture.__init__(self, _artnet, name, universe=universe)
        self._display = SevenSegment(digits, cs=pin_chip_select, spi_bus=hardware_spi, reverse=True)

    def parse_dmx_data(self, data: bytes) -> None:
        brightness: int = data[0] // 16
        self._display.text(data[1:].decode("ascii"))
        self._display.brightness(brightness)
