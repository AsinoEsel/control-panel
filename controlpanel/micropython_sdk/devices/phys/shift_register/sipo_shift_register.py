from machine import Pin
import asyncio
from ...base.shift_register import BaseSipoShiftRegister
from .shift_register import ShiftRegister


class SipoShiftRegister(BaseSipoShiftRegister, ShiftRegister):
    def __init__(self, artnet, name: str, clock: int, latch: int, serialout: int, count: int = 1, *, universe: int | None = None, remapping: list[int | None] | None = None):
        BaseSipoShiftRegister.__init__(self, artnet, name, count, universe=universe, remapping=remapping)
        ShiftRegister.__init__(self, count, latch, clock)
        self._serialout_pin: Pin = Pin(serialout, Pin.OUT)

    def _update_states(self):
        for i in range(self._number_of_bits):
            self._serialout_pin.value(self._output_states[self._number_of_bits - 1 - i])
            self._shift()
        self._latch()
    
    def update(self):
        self._update_states()

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
            