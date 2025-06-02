from controlpanel.shared.base.bvg_panel import BaseBVGPanel
from controlpanel.event_manager.dummy import FixtureMixin


class BVGPanel(BaseBVGPanel, FixtureMixin):
    def __setitem__(self, index, value: int | bool):
        super().__setitem__(index, value)
        self.send_dmx_data()
