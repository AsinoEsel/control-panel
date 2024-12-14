from controlpanel.shared.base.shift_register import BaseSipoShiftRegister


class DummySipoShiftRegister(BaseSipoShiftRegister):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data()
