from controlpanel.shared.base.seven_segment import BaseSevenSegmentDisplay


class DummySevenSegmentDisplay(BaseSevenSegmentDisplay):
    def __init__(self, artnet, name: str, digits: int):
        super().__init__(artnet, name)
        self._text: str = ""
        self._digits = digits

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, txt: str):
        self._text = txt[:self._digits]
        self.send_dmx_data(txt.encode('ASCII'))
