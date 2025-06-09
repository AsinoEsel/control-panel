import neopixel
from machine import Pin
from controlpanel.shared.base.led_strip import BaseLEDStrip, Generator, Literal
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
                 update_rate_hz: float = 1.0,
                 rgb_order: Literal["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"] = "RGB",  # used for animations
                 ) -> None:
        BaseLEDStrip.__init__(self, rgb_order)
        Fixture.__init__(self, _artnet, name, update_rate_hz, universe=universe)
        self._neopixels: neopixel.NeoPixel = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)
        self._use_compression = use_compression
        self._animation: Generator[bytearray, None, None] | None = None

    def __len__(self):
        return len(self._neopixels)

    @staticmethod
    def _uncompress_rgb_into(buffer: bytearray, compressed: bytes | memoryview) -> None:
        """
        Convert a bytes object containing compressed RGB values (RRRGGGBB)
        into a bytearray where each byte is a separate color channel.
        """
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
            buffer[3 * i] = r
            buffer[3 * i + 1] = g
            buffer[3 * i + 2] = b

    def parse_dmx_data(self, data: bytes):
        animation_index = data[0]
        if animation_index == 0:
            self._animation = None
        elif animation_index > len(self.ANIMATIONS):
            print("Invalid animation index")
            return
        else:
            self._animation = self.ANIMATIONS[animation_index](self.update_rate_ms, self._neopixels.buf, self._rgb_mapping)
            return

        if len(data) == 1:
            return

        if not self._use_compression:
            assert len(data) == 1 + 3 * len(self._neopixels), "length of data must be 1 plus 3 times the number of pixels"
            self._neopixels.buf = bytearray(memoryview(data)[1:])
        else:
            assert len(data) == 1 + len(self._neopixels), "length of data must be equal to the number of pixels plus 1"
            self._uncompress_rgb_into(self._neopixels.buf, memoryview(data)[1:])
        self._neopixels.write()

    async def update(self):
        if not self._animation:
            return
        try:
            next(self._animation)
            self._neopixels.write()
        except StopIteration:
            self._animation = None
