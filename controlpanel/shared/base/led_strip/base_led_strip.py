from ..fixture import Fixture
try:
    from micropython import const
except ImportError:
    const = lambda x: x


BITMASK_RED = const(0b11100000)
BITMASK_GREEN = const(0b00011100)
BITMASK_BLUE = const(0b00000011)


class BaseLEDStrip(Fixture):
    DMX_INDEX_ANIMATION = const(0)
    DMX_STARTINDEX_PIXELS = const(1)
    RGB_CHANNEL_ORDER = (0, 1, 2)

    def __init__(self, artnet, name: str, *, universe: int | None = None) -> None:
        super().__init__(artnet, name, universe=universe)
        self._animation_index: int = 0

    @staticmethod
    def compress_rgb(rgb: tuple[int, int, int]) -> int:
        """
        Convert an RGB tuple (R, G, B) with values in the range 0..255
        into a single RGB byte in the format RRRGGGBB.
        """
        r, g, b = rgb
        r = (r >> 5) & 0x07  # Take the top 3 bits of R
        g = (g >> 5) & 0x07  # Take the top 3 bits of G
        b = (b >> 6) & 0x03  # Take the top 2 bits of B
        return (r << 5) | (g << 2) | b

    @staticmethod
    def decompress_rgb(compressed: bytes) -> bytearray:
        """
        Convert a bytes object containing compressed RGB values (RRRGGGBB)
        into a bytearray where each byte is a separate color channel.
        """
        result = bytearray(len(compressed) * 3)
        for i, byte in enumerate(compressed):
            # Extract R, G, B values
            r = (byte & BITMASK_RED) >> 5  # Top 3 bits for R
            g = (byte & BITMASK_GREEN) >> 2  # Middle 3 bits for G
            b = byte & BITMASK_BLUE  # Bottom 2 bits for B

            # Scale them back to the 0-255 range
            r = (r << 5) | (r << 2) | (r >> 1)  # Scale 3-bit to 8-bit
            g = (g << 5) | (g << 2) | (g >> 1)  # Scale 3-bit to 8-bit
            b = (b << 6) | (b << 4) | (b << 2) | b  # Scale 2-bit to 8-bit

            # Append the expanded channels
            result[3*i] = r
            result[3*i + 1] = g
            result[3*i + 2] = b

        return result

    def __len__(self):
        raise NotImplementedError("Needs to be implemented by subclass!")
