from machine import Pin, SoftSPI, I2C
from controlpanel.shared.base.shift_registers import BasePisoShiftRegister, BaseSipoShiftRegister
from .sensor import Sensor
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet
from time import sleep_us


class PisoShiftRegister(BasePisoShiftRegister, Sensor):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 latch: int,
                 count: int = 1,
                 *,
                 polling_rate_hz: float = BasePisoShiftRegister.DEFAULT_POLLING_RATE_HZ,
                 ) -> None:
        Sensor.__init__(self, _context[0], _name, polling_rate_hz)
        self._spi: SoftSPI = _context[1]
        self._latch_pin: Pin = Pin(latch, Pin.OUT)
        self._count = count
        self._input_states = bytearray(0 for _ in range(self._count))

    def _read_states(self):
        changed_states = bytearray()

        # Latch current inputs from the shift registers
        self._latch_pin.value(0)
        sleep_us(5)
        self._latch_pin.value(1)

        # Read new states from SPI
        new_states = self._spi.read(self._count, 0x42)

        # Compare new states with previous ones
        for byte_index in range(self._count):
            old_byte = self._input_states[byte_index]
            new_byte = new_states[byte_index]

            if old_byte != new_byte:
                # Compare each bit to detect which inputs changed
                for bit_index in range(8):
                    old_bit = (old_byte >> bit_index) & 1
                    new_bit = (new_byte >> bit_index) & 1
                    if old_bit != new_bit:
                        button_id = byte_index * 8 + bit_index
                        changed_states.append(button_id)
                        changed_states.append(new_bit)

        # Update stored states
        self._input_states[:] = new_states

        # Send packet if there are changes
        if changed_states:
            print(changed_states)
            self._send_trigger_packet(changed_states)

    async def update(self) -> None:
        self._read_states()


class SipoShiftRegister(BaseSipoShiftRegister, Fixture):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 latch: int,
                 count: int = 1,
                 *,
                 update_rate_hz: float = BaseSipoShiftRegister.DEFAULT_UPDATE_RATE_HZ,
                 universe: int | None = None,
                 ) -> None:
        Fixture.__init__(self, _context[0], _name, update_rate_hz, universe=universe)
        self._spi: SoftSPI = _context[1]
        self._latch_pin: Pin = Pin(latch, Pin.OUT)
        self._number_of_bits = count * 8

    def _write_states(self, data: bytes) -> None:
        raise NotImplementedError  # TODO: Restore functionality!

    def parse_dmx_data(self, data: bytes):
        assert len(data) == self._number_of_bits
        self._write_states(data)
