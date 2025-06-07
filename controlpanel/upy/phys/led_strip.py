import neopixel
from machine import Pin
from controlpanel.shared.base.led_strip import BaseLEDStrip
from .fixture import Fixture
from controlpanel.shared.compatibility import ArtNet
from micropython import const


_BITMASK_RED = const(0b11100000)
_BITMASK_GREEN = const(0b00011100)
_BITMASK_BLUE = const(0b00000011)


class LEDStrip(BaseLEDStrip, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 pin: int,
                 length: int,
                 *,
                 universe: int | None = None,
                 use_compression: bool = False,
                 ) -> None:
        Fixture.__init__(self, _artnet, name, universe=universe)
        self._neopixels: neopixel.NeoPixel = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)
        self._use_compression = use_compression

    def __len__(self):
        return len(self._neopixels)

    @staticmethod
    def _uncompress_rgb(compressed: bytes) -> bytearray:
        """
        Convert a bytes object containing compressed RGB values (RRRGGGBB)
        into a bytearray where each byte is a separate color channel.
        """
        result = bytearray(len(compressed) * 3)
        for i, byte in enumerate(compressed):
            # Extract R, G, B values
            r = (byte & _BITMASK_RED) >> 5  # Top 3 bits for R
            g = (byte & _BITMASK_GREEN) >> 2  # Middle 3 bits for G
            b = byte & _BITMASK_BLUE  # Bottom 2 bits for B

            # Scale them back to the 0-255 range
            r = (r << 5) | (r << 2) | (r >> 1)  # Scale 3-bit to 8-bit
            g = (g << 5) | (g << 2) | (g >> 1)  # Scale 3-bit to 8-bit
            b = (b << 6) | (b << 4) | (b << 2) | b  # Scale 2-bit to 8-bit

            # Append the expanded channels
            result[3 * i] = r
            result[3 * i + 1] = g
            result[3 * i + 2] = b

        return result

    def parse_dmx_data(self, data: bytes):
        if not self._use_compression:
            assert len(data) == 3 * len(self._neopixels), "length of data must be 3 times the number of pixels"
            self._neopixels.buf = bytearray(data)
        else:
            assert len(data) == len(self._neopixels), "length of data must be equal to the number of pixels"
            self._neopixels.buf = self._uncompress_rgb(data)
        self._neopixels.write()
