import math

from ..sensor import Sensor
from .base_shift_register import BaseShiftRegister


class BasePisoShiftRegister(Sensor, BaseShiftRegister):
    SUBKEY = 8

    def __init__(self, artnet, name: str, count=1, *, callback=None, remapping: list[int] | None = None):
        super().__init__(artnet, name, callback=callback)
        BaseShiftRegister.__init__(self, count, remapping=remapping)
        self._input_states: list[int] = [0 for _ in range(count * 8)]

    def __getitem__(self, index) -> bool:
        if self._remapping is not None:
            index = self._remapping[index]
        return bool(self._input_states[index])

    def get_payload(self) -> bytes:
        result = bytearray(math.ceil(len(self._input_states) / 8))
        for i, bit in enumerate(self._input_states):
            if bit:
                idx = i // 8
                pos = i % 8
                bit_value = 0b1 << pos
                result[idx] |= bit_value
        return bytes(result)

    def parse_trigger_data(self, data: bytes):
        for i in range(self._number_of_bits):
            byte_index = i // 8
            bit_position = i % 8
            if data[byte_index] & (1 << bit_position):
                self._input_states[i] = 1
            else:
                self._input_states[i] = 0
        print("Parsing Trigger:")
        print(self._input_states)

    def update(self):
        raise NotImplementedError("Needs to be implemented by subclass.")
