from controlpanel.shared.base.pwm import BasePWM


class DummyPWM(BasePWM):
    def __init__(self, artnet, name: str, intensity: float = 1.0):
        super().__init__(artnet, name)
        self._intensity = intensity

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, val: float):
        assert 0.0 <= val <= 1.0
        self._intensity = val
        self.send_dmx_data(int(val * 255).to_bytes())

    def blackout(self) -> None:
        self.intensity = 0.0
