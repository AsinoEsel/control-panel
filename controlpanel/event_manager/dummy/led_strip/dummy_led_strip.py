from controlpanel.shared.base.led_strip import BaseLEDStrip


class DummyLEDStrip(BaseLEDStrip):
    def __init__(self, artnet, name: str, length: int, *, universe=None, animation=None) -> None:
        super().__init__(artnet, name, universe=universe)
        self._pixels: list[tuple[int, int, int]] = [(0, 0, 0) for _ in range(length)]

    def __len__(self):
        return len(self._pixels)

    def __getitem__(self, item):
        return self._pixels[item]

    def __setitem__(self, key, value):
        self._pixels[key] = value
        self.send_dmx_data(bytes(value for rgb in self._pixels for value in rgb))
