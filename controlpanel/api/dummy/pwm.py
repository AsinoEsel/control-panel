from controlpanel.shared.base.pwm import BasePWM
from .fixture import Fixture
from artnet import ArtNet


class PWM(BasePWM, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 *,
                 intensity: float = 1.0,
                 universe: int | None = None,
                 ) -> None:
        Fixture.__init__(self, _artnet, name, universe=universe)
        self._intensity: float = intensity

    @property
    def intensity(self) -> float:
        return self._intensity

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_intensity(value)

    def get_intensity(self) -> float:
        return self._intensity

    def set_intensity(self, intensity: float) -> None:
        intensity = min(max(intensity, 0.0), 1.0)
        self._intensity = intensity
        self._send_dmx_packet(int(intensity * 255).to_bytes())

    def blackout(self) -> None:
        self.set_intensity(0.0)

    def whiteout(self) -> None:
        self.set_intensity(1.0)
