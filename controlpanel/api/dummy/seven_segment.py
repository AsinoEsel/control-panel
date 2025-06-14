from controlpanel.shared.base.seven_segment import BaseSevenSegmentDisplay
from .fixture import Fixture
from artnet import ArtNet


class SevenSegmentDisplay(BaseSevenSegmentDisplay, Fixture):
    def __init__(self, _artnet: ArtNet, name: str, digit_count: int, *, universe: int | None = None):
        Fixture.__init__(self, _artnet, name, universe=universe)
        self._text: str = ""
        self._digit_count = digit_count
        self._brightness: int = 7

    def display_text(self, text: str) -> None:
        self._text = text[:self._digit_count]
        self._send_dmx_packet(self._brightness.to_bytes() + self._text.encode('ASCII'))

    def set_brightness(self, brightness: float = 0.5) -> None:
        brightness = max(0.0, min(1.0, brightness))
        self._brightness = int(brightness * 15)
        self._send_dmx_packet(self._brightness.to_bytes() + self._text.encode('ASCII'))

    def whiteout(self) -> None:
        brightness: int = 15
        text: str = ("8" * self._digit_count)
        self._send_dmx_packet(brightness.to_bytes() + text.encode('ASCII'))

    def blackout(self) -> None:
        text: str = ""
        self._send_dmx_packet(self._brightness.to_bytes() + text.encode('ASCII'))
