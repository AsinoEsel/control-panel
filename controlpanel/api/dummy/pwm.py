import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .esp32 import ESP32


class PWM(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 _name: str,
                 /,
                 *,
                 intensity: float = 1.0,
                 universe: int | None = None,
                 ) -> None:
        Fixture.__init__(self, _artnet, _loop, _esp, _name, universe=universe)
        self._intensity: float = intensity

    def send_dmx(self) -> None:
        self._send_dmx_packet(int(self._intensity * 255).to_bytes())

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
        self.send_dmx()

    def blackout(self) -> None:
        self.set_intensity(0.0)

    def whiteout(self) -> None:
        self.set_intensity(1.0)
