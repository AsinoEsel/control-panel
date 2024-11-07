from ...base.led_strip import BaseLEDStrip


class DummyLEDStrip(BaseLEDStrip):
    def __init__(self, artnet, name: str, length: int, *, universe=None, animation=None) -> None:
        super().__init__(artnet, name, universe=universe, animation=animation)
        self._length = length
        self._buffer = bytearray(3*length)

    def __len__(self):
        return self._length

    @property
    def buffer(self):
        return self._buffer

    @buffer.setter
    def buffer(self, buf: bytearray):
        self._buffer = buf

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.send_dmx_data()

    def get_dmx_data(self) -> bytearray:
        return self.buffer

    def parse_dmx_data(self, data: bytes):
        self.buffer = bytearray(data)



