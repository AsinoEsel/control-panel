from ...base.seven_segment import BaseSevenSegmentDisplay


class DummySevenSegmentDisplay(BaseSevenSegmentDisplay):
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, txt: str):
        self._text = txt
        self.send_dmx_data()
