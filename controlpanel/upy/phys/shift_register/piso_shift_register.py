from machine import Pin
import asyncio
from controlpanel.shared.base.shift_register import BasePisoShiftRegister
from controlpanel.upy.phys import SensorMixin
from .shift_register import ShiftRegister


class PisoShiftRegister(BasePisoShiftRegister, ShiftRegister, SensorMixin):
    def __init__(self, artnet, name: str, clock: int, latch: int, serialin: int, count: int = 1, *, remapping: list[int] | None = None):
        BasePisoShiftRegister.__init__(self, artnet, name, count, remapping=remapping)
        ShiftRegister.__init__(self, count, latch, clock)
        self._serialin_pin: Pin = Pin(serialin, Pin.IN)  # Button states (0 == pressed)

    def update(self):
        self._latch()
        changed_states: bytearray = bytearray()
        for i in range(self._number_of_bits):
            old_state = self._input_states[i]
            new_state = self._serialin_pin.value()
            self._input_states[i] = new_state
            if old_state != new_state:
                changed_states.append(i)
                changed_states.append(new_state)
                # print(f"State of {i} changed to {new_state}.")
            self._shift()
        if changed_states:
            # print(f"Update: {changed_states}")
            self.send_trigger(changed_states)

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
            