from controlpanel.shared.base.seven_segment import BaseSevenSegmentDisplay
from controlpanel.event_manager.dummy import FixtureMixin


class SevenSegmentDisplay(BaseSevenSegmentDisplay, FixtureMixin):
    def __init__(self, artnet, name: str, digit_count: int):
        super().__init__(artnet, name)
        self._text: str = ""
        self._digit_count = digit_count

    @property
    def text(self):
        return self._text

    def display_text(self, text: str):
        self._text = text[:self._digit_count]
        self.send_dmx_data(text.encode('ASCII'))
