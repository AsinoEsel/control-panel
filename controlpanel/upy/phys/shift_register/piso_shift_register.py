from machine import Pin
import asyncio
from controlpanel.shared.base.shift_register import BasePisoShiftRegister
from .shift_register import ShiftRegister


class PisoShiftRegister(BasePisoShiftRegister, ShiftRegister):
    def __init__(self, artnet, name: str, clock: int, latch: int, serialin: int, count: int = 1, *, remapping: list[int] | None = None):
        BasePisoShiftRegister.__init__(self, artnet, name, count, remapping=remapping)
        ShiftRegister.__init__(self, count, latch, clock)
        self._serialin_pin: Pin = Pin(serialin, Pin.IN)  # Button states (0 == pressed)

    def _update_states(self):
        self._latch()
        for i in range(self._number_of_bits):
            self._input_states[i] = self._serialin_pin.value()
            self._shift()

    def update(self):
        old_states = self._input_states[::]
        self._update_states()
        state_changed = False
        for i in range(self._number_of_bits):  # TODO: just compare lists instead!?
            if old_states[i] != self._input_states[i]:
                state_changed = True
        if state_changed:
            self.send_trigger_data(bytes(self._input_states))

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
            