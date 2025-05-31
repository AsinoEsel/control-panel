from controlpanel.shared.base.bvg_panel import BaseBVGPanel


class BVGPanel(BaseBVGPanel):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data()
