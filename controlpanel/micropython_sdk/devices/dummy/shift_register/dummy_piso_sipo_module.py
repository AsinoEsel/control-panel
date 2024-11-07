from ...base.shift_register import BasePisoSipoModule


class DummyPisoSipoModule(BasePisoSipoModule):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data()
