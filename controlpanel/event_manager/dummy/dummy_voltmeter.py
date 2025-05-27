from controlpanel.shared.base.voltmeter import BaseVoltmeter


class DummyVoltmeter(BaseVoltmeter):
    def __init__(self, artnet, name: str, intensity: float = 1.0, *, universe: int | None = None):
        super().__init__(artnet, name, universe=universe)
        self._intensity = intensity

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, val: float):
        assert 0.0 <= val <= 1.0
        self._intensity = val
        self.send_dmx_data(int(val * 255).to_bytes())
