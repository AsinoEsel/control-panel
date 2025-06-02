from controlpanel.shared.base.led_strip import BaseLEDStrip
from controlpanel.event_manager.dummy import FixtureMixin


class LEDStrip(BaseLEDStrip, FixtureMixin):
    def __init__(self, artnet, name: str, length: int, *, universe=None) -> None:
        super().__init__(artnet, name, universe=universe)
        self._pixels: list[tuple[int, int, int]] = [(0, 0, 0) for _ in range(length)]

    def __len__(self):
        return len(self._pixels)

    def __getitem__(self, item):
        return self._pixels[item]

    def __setitem__(self, key, value):
        assert isinstance(value, tuple) and len(value) == 3 and all(0 <= val <= 255 for val in value)
        self._pixels[key] = value
        self.send_dmx_data(self._animation_index.to_bytes() + bytes(value for rgb in self._pixels for value in rgb))

    def set_animation(self, animation_index: int):
        self._animation_index = animation_index
        self.send_dmx_data(self._animation_index.to_bytes())

    def set_pixel(self, pixel: int, color: tuple[int, int, int], *, override_animation: bool = True):
        if override_animation:
            self._animation_index = 0
        self._pixels[pixel] = color
        self.send_dmx_data(self._animation_index.to_bytes() + bytes(self.compress_rgb(color) for color in self._pixels))
        self.send_dmx_data(self._animation_index.to_bytes() + bytes(value for rgb in self._pixels for value in rgb))

    def fill(self, color: tuple[int, int, int], *, override_animation: bool = True):
        if override_animation:
            self._animation_index = 0
        self._pixels = [color for _ in range(len(self._pixels))]
        compressed_color: int = self.compress_rgb(color)
        self.send_dmx_data(self._animation_index.to_bytes() + bytearray(compressed_color for _ in range(len(self._pixels))))
    #
    def blackout(self):
        self._pixels = [(0, 0, 0) for _ in self._pixels]
        self.send_dmx_data(self._animation_index.to_bytes() + bytearray(self.compress_rgb(color) for color in self._pixels))
