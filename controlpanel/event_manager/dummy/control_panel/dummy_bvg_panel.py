from controlpanel.shared.base.control_panel import BaseBVGPanel


class DummyBVGPanel(BaseBVGPanel):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data()
