from .fixture import Fixture


class BaseSevenSegmentDisplay(Fixture):
    def __init__(self, artnet, name: str, *, universe: int | None = None) -> None:
        super().__init__(artnet, name, universe=universe)
