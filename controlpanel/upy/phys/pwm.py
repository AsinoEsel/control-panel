import machine
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet
from micropython import const


_DEFAULT_UPDATE_RATE_HZ = const(2.0)


class PWM(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            pin: int,
            *,
            update_rate_hz: int = _DEFAULT_UPDATE_RATE_HZ,
            universe: int | None = None,
            intensity: float = 0.5,
            freq: int = 512,
        ) -> None:
        super().__init__(_context[0], _name, update_rate_hz, universe=universe)
        self.pin = machine.Pin(pin)
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(freq)
        self.pwm.duty(int(1023 * intensity))

    @staticmethod
    def get_duty(intensity: float) -> int:
        return min(1023, max(0, int(1023*intensity)))

    def set_intensity(self, intensity: float) -> None:
        self.pwm.duty(self.get_duty(intensity))

    def parse_dmx_data(self, data: bytes):
        intensity = data[0] / 255
        self.set_intensity(intensity)
