from ..fixture import Fixture


class BaseSevenSegmentDisplay(Fixture):
    def __init__(self, artnet, name: str, text: str = "", *, universe: int | None = None) -> None:
        super().__init__(artnet, name, universe=universe)
        self._text: str = text

    def update(self):
        # TODO: Animations
        pass

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, txt: str):
        self._text = txt

    def get_dmx_data(self) -> bytearray:
        return bytearray(self.text.encode())

    def parse_dmx_data(self, data: bytes):
        self.text = data.decode("ascii")
