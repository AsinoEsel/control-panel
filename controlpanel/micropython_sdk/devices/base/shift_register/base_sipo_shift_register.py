from ..fixture import Fixture
from .base_shift_register import BaseShiftRegister


class BaseSipoShiftRegister(Fixture, BaseShiftRegister):
    def __init__(self, artnet, name: str, count=1, *, universe: int | None = None, remapping: list[int | None] | None = None):
        super().__init__(artnet, name, universe=universe)
        BaseShiftRegister.__init__(self, count, remapping=remapping)
        self._output_states: list[int] = [0 for _ in range(count * 8)]

    def __setitem__(self, index, value: int | bool):
        if isinstance(index, slice):
            if isinstance(index, slice):
                start, stop, step = index.indices(self._number_of_bits)
                for i in range(start, stop, step):
                    if self._remapping is not None:
                        i = self._remapping[i]
                    self._output_states[i] = 1 if value else 0
        else:
            if self._remapping is not None:
                index = self._remapping[index]
                if index is None:
                    return
            self._output_states[index] = 1 if value else 0

    def parse_dmx_data(self, data: bytes):
        for i, byte in enumerate(data):
            if self._remapping is not None:
                i = self._remapping[i]
                if i is None:
                    continue
            self._output_states[i] = 1 if byte else 0

    def get_dmx_data(self) -> bytearray:
        return bytearray(255 if bit else 0 for bit in self._output_states)

    def update(self):
        raise NotImplementedError("Needs to be implemented by subclass.")
