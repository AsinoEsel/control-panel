from ..fixture import Fixture
try:
    from micropython import const
except ImportError:
    const = lambda x: x


class BaseLEDStrip(Fixture):
    DMX_INDEX_ANIMATION = const(0)
    DMX_STARTINDEX_PIXELS = const(1)
    RGB_CHANNEL_ORDER = (0, 1, 2)

    def __init__(self, artnet, name: str, *, universe: int | None = None) -> None:
        super().__init__(artnet, name, universe=universe)

    def __len__(self):
        raise NotImplementedError("Needs to be implemented by subclass!")
