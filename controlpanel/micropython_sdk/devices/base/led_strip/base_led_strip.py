from ..fixture import Fixture


class BaseLEDStrip(Fixture):
    RGB_CHANNEL_ORDER = (0, 1, 2)

    def __init__(self, artnet, name: str, *, universe: int | None = None, animation=None) -> None:
        super().__init__(artnet, name, universe=universe)
        self._animation = animation

    def __len__(self):
        raise NotImplementedError("Needs to be implemented by subclass!")

    @property
    def buffer(self):
        raise NotImplementedError("Needs to be implemented by subclass")

    @buffer.setter
    def buffer(self, buf: bytearray):
        raise NotImplementedError("Needs to be implemented by subclass")

    def __getitem__(self, item: int | slice) -> tuple[int, int, int] | list[tuple[int, int, int]]:
        if isinstance(item, slice):
            start, stop, step = item.indices(len(self.buffer) // 3)
            return [tuple(self.buffer[3 * i + channel] for channel in self.RGB_CHANNEL_ORDER) for i in range(start, stop, step)]
        else:
            return tuple(self.buffer[3 * item + channel] for channel in self.RGB_CHANNEL_ORDER)

    def __setitem__(self, key: int | slice, value: tuple[int, int, int]):
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            for i in range(start, stop, step):
                for channel in self.RGB_CHANNEL_ORDER:
                    self.buffer[i * 3 + channel] = value[channel]
        else:
            for channel in self.RGB_CHANNEL_ORDER:
                self.buffer[key*3 + channel] = value[channel]

    def get_dmx_data(self) -> bytearray:
        return self.buffer

    def parse_dmx_data(self, data: bytes):
        self.buffer = bytearray(data)

    def update(self):
        if self._animation:
            buf = next(self._animation)
            if buf is not None:
                self.buffer = buf
