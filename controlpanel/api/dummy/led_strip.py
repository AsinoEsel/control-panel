from controlpanel.shared.base.led_strip import BaseLEDStrip
from .fixture import Fixture
from typing import SupportsIndex, Literal, Callable
from artnet import ArtNet


class _Pixels:
    """A proxy class for the pixel list.
    Automatically calls the update_callback function when a value in the list is changed."""
    def __init__(self, pixels: list[tuple[int, int, int]], update_callback: Callable[[], None]):
        self._pixels = pixels
        self._update_callback = update_callback

    def __getitem__(self, key):
        return self._pixels[key]

    def __setitem__(self, key, value):
        self._pixels[key] = value
        self._update_callback()

    def __len__(self):
        return len(self._pixels)

    def __iter__(self):
        return iter(self._pixels)

    def __repr__(self):
        return repr(self._pixels)

    def __getslice__(self, i, j):
        return self._pixels[i:j]

    def __setslice__(self, i, j, sequence):
        self._pixels[i:j] = sequence
        self._update_callback()

    def __eq__(self, other):
        return self._pixels == other


class LEDStrip(BaseLEDStrip, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 length: int,
                 *,
                 universe=None,
                 rgb_order: Literal["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"] = "RGB",
                 use_compression: bool = False
                 ) -> None:
        BaseLEDStrip.__init__(self, rgb_order)
        Fixture.__init__(self, _artnet, name, universe=universe)
        self._pixel_proxy: _Pixels = _Pixels([(0, 0, 0) for _ in range(length)], self._send_pixel_data)
        self._use_compression: bool = use_compression
        self._animation_index: int = 0

    def set_animation(self, animation_index: int):
        self._animation_index = animation_index
        self._send_dmx_data(self._animation_index.to_bytes())

    @staticmethod
    def _compress_rgb(rgb: tuple[int, int, int]) -> int:
        """
        Convert an RGB tuple (R, G, B) with values in the range 0..255
        into a single RGB byte in the format RRRGGGBB.
        """
        r, g, b = rgb
        r = (r >> 5) & 0x07  # Take the top 3 bits of R
        g = (g >> 5) & 0x07  # Take the top 3 bits of G
        b = (b >> 6) & 0x03  # Take the top 2 bits of B
        return (r << 5) | (g << 2) | b

    def _send_pixel_data(self):
        self._animation_index = 0
        self._send_dmx_data(self._pack_pixel_bytes())

    def _reorder_rgb(self, rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        return rgb[self._rgb_mapping[0]], rgb[self._rgb_mapping[1]], rgb[self._rgb_mapping[2]]

    def _pack_pixel_bytes(self) -> bytes:
        if not self._use_compression:
            return b"\x00" + bytes(value for rgb in self._pixel_proxy for value in self._reorder_rgb(rgb))
        else:
            return b"\x00" + bytes(self._compress_rgb(self._reorder_rgb(rgb)) for rgb in self._pixel_proxy)

    def __len__(self):
        return len(self._pixel_proxy)

    def __getitem__(self, item) -> tuple[int, int, int]:
        return self._pixel_proxy[item]

    def __setitem__(self, pixel: SupportsIndex, rgb: tuple[int, int, int]) -> None:
        self.set_pixel(pixel, rgb)

    def __iter__(self):
        return iter(self._pixel_proxy)

    @property
    def pixels(self) -> _Pixels:
        return self._pixel_proxy

    @pixels.setter
    def pixels(self, new_pixels: list[tuple[int, int, int]]):
        if not isinstance(new_pixels, list):
            raise TypeError("Pixels must be assigned a list of (R, G, B) tuples.")
        if len(new_pixels) != len(self):
            raise ValueError(f"Pixel list must be exactly {len(self)} items long.")
        if not all(
                isinstance(rgb, tuple) and len(rgb) == 3 and all(0 <= val <= 255 for val in rgb) for rgb in new_pixels):
            raise ValueError("Each pixel must be a tuple of three integers between 0 and 255.")
        self._pixel_proxy[:] = new_pixels  # Update the existing Pixels proxy in-place so references don't break

    def set_pixel(self, pixel: SupportsIndex, rgb: tuple[int, int, int]):
        assert isinstance(rgb, tuple) and len(rgb) == 3 and all(0 <= val <= 255 for val in rgb), "Invalid rgb tuple"
        self._pixel_proxy[pixel] = rgb
        self._send_pixel_data()

    def set_pixels(self, pixels: list[tuple[int, int, int]]):
        self.pixels = pixels

    def fill(self, color: tuple[int, int, int]):
        self._pixel_proxy[:] = [color] * len(self)

    def blackout(self) -> None:
        self.fill((0, 0, 0))

    def whiteout(self) -> None:
        self.fill((255, 255, 255))
