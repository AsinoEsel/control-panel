from .piso_shift_register import PisoShiftRegister
from .sipo_shift_register import SipoShiftRegister


class PisoSipoModule(PisoShiftRegister, SipoShiftRegister):
    def __init__(self,
                 artnet,
                 name: str,
                 clock: int,
                 latch: int,
                 serial_in: int,
                 serial_out: int,
                 count: int = 1,
                 *,
                 universe: int | None = None,
                 piso_remapping: list[int | None] | None = None,
                 sipo_remapping: list[int | None] | None = None):
        PisoShiftRegister.__init__(self, artnet, name, clock, latch, serial_in, count, remapping=piso_remapping)
        SipoShiftRegister.__init__(self, artnet, name, clock, latch, serial_out, count, universe=universe, remapping=sipo_remapping)
        self._piso_remapping = piso_remapping
        self._sipo_remapping = sipo_remapping

    def _update_states(self):
        self._latch()
        for i in range(self._number_of_bits):
            self._input_states[i] = self._serialin_pin.value()
            self._serialout_pin.value(self._output_states[self._number_of_bits - 1 - i])
            self._shift()
        self._latch()

    def update(self):
        old_states = self._input_states[::]
        self._update_states()
        for i in range(self._number_of_bits):
            if old_states[i] != self._input_states[i]:
                self.send_trigger_data(bytes(self._input_states))
