from machine import Pin
from controlpanel.shared.base.shift_registers import BasePisoShiftRegister, BaseSipoShiftRegister, BasePisoSipoModule
from controlpanel.upy.artnet import ArtNet
from .sensor import Sensor
from .fixture import Fixture
from micropython import const
from time import sleep_us


class ShiftRegister:
    SLEEP_TIME_US = const(3)  # TODO: check if smaller values work  # 5

    def __init__(self, count: int, clock_pin: int, latch_pin: int):
        self._number_of_bits: int = count * 8
        self._latch_pin: Pin = Pin(latch_pin, Pin.OUT)
        self._clock_pin: Pin = Pin(clock_pin, Pin.OUT)

    def _shift(self):
        self._clock_pin.value(0)
        sleep_us(self.SLEEP_TIME_US)
        self._clock_pin.value(1)
        sleep_us(self.SLEEP_TIME_US)

    def _latch(self):
        self._latch_pin.value(0)
        sleep_us(self.SLEEP_TIME_US)
        self._latch_pin.value(1)
        sleep_us(self.SLEEP_TIME_US)


class PisoShiftRegister(BasePisoShiftRegister, ShiftRegister, Sensor):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 pin_clock: int,
                 pin_latch: int,
                 pin_serialin: int,
                 count: int = 1
                 ) -> None:
        Sensor.__init__(self, _artnet, name)
        ShiftRegister.__init__(self, count, pin_clock, pin_latch)
        self._serialin_pin: Pin = Pin(pin_serialin, Pin.IN)  # Button states (0 == pressed)
        self._input_states = bytearray(0 for _ in range(self._number_of_bits))

    def _read_states(self):
        self._latch()
        changed_states: bytearray = bytearray()
        for i in range(self._number_of_bits):
            old_state = self._input_states[i]
            new_state = self._serialin_pin.value()
            self._input_states[i] = new_state
            if old_state != new_state:
                changed_states.append(i)
                changed_states.append(new_state)
            self._shift()
        if changed_states:
            self.send_trigger(changed_states)

    async def poll(self) -> None:
        self._read_states()


class SipoShiftRegister(BaseSipoShiftRegister, ShiftRegister, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 pin_clock: int,
                 pin_latch: int,
                 pin_serialout: int,
                 count: int = 1,
                 *,
                 universe: int | None = None,
                 ) -> None:
        Fixture.__init__(self, _artnet, name, universe=universe)
        ShiftRegister.__init__(self, count, pin_clock, pin_latch)
        self._serialout_pin: Pin = Pin(pin_serialout, Pin.OUT)  # Button states (0 == pressed)

    def _write_states(self, data: bytes) -> None:
        for i in range(self._number_of_bits):
            self._serialout_pin.value(data[self._number_of_bits - 1 - i])
            self._shift()
        self._latch()

    def parse_dmx_data(self, data: bytes):
        assert len(data) == self._number_of_bits
        self._write_states(data)
