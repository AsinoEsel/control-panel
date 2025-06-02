from controlpanel.shared.base.shift_register import BasePisoSipoModule
from controlpanel.event_manager.dummy import FixtureMixin, SensorMixin


class PisoSipoModule(BasePisoSipoModule, FixtureMixin, SensorMixin):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data(self.get_dmx_data())

    def parse_trigger_data(self, data: bytes) -> tuple[str, bytes]:
        self._input_states = [byte for byte in data]
        return "ButtonsChanged", data
