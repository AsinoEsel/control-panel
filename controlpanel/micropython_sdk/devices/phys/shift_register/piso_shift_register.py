from machine import Pin
import asyncio
from ...base.shift_register import BasePisoShiftRegister
from .shift_register import ShiftRegister


class PisoShiftRegister(BasePisoShiftRegister, ShiftRegister):
    def __init__(self, artnet, name: str, clock: int, latch: int, serialin: int, count: int = 1, *, callback=None, remapping: list[int] | None = None):
        BasePisoShiftRegister.__init__(self, artnet, name, count, callback=callback, remapping=remapping)
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
        for i in range(self._number_of_bits):
            if old_states[i] != self._input_states[i]:
                self.callback(i, not self._input_states[i])

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
            