from ...base.shift_register import BaseShiftRegister
from machine import Pin
from time import sleep_us
from micropython import const


class ShiftRegister(BaseShiftRegister):
    SLEEP_TIME_US = const(5)  # TODO: check if smaller values work

    def __init__(self, count: int, latch_pin: int, clock_pin: int):
        super().__init__(count)
        self._latch_pin: Pin = Pin(latch_pin, Pin.OUT)
        self._clock_pin: Pin = Pin(clock_pin, Pin.OUT)

    def _shift(self):
        self._clock_pin.value(0)
        sleep_us(self.SLEEP_TIME_US)
        self._clock_pin.value(1)

    def _latch(self):
        self._latch_pin.value(0)
        sleep_us(self.SLEEP_TIME_US)
        self._latch_pin.value(1)

    def _update_states(self):
        raise NotImplementedError("Needs to be implemented by subclass!")
