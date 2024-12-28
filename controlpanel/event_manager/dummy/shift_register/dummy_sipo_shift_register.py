from controlpanel.shared.base.shift_register import BaseSipoShiftRegister


class DummySipoShiftRegister(BaseSipoShiftRegister):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data(bytes(self._output_states))

    def blackout(self):
        self.send_dmx_data(bytes(self._number_of_bits))

    def whiteout(self) -> None:
        self.send_dmx_data(b"\xff" * self._number_of_bits)

    def set_bit(self, bit: int):
        self._output_states[bit] = 255
        self.send_dmx_data(bytes(self._output_states))
