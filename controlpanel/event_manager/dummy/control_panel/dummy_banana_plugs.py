from controlpanel.shared.base.control_panel import BaseBananaPlugs


class DummyBananaPlugs(BaseBananaPlugs):
    def __init__(self, artnet, name: str, plug_count: int):
        super().__init__(artnet, name, plug_count)

    def parse_trigger_data(self, data: bytes):
        assert len(data) == 2
        plug_idx, socket_idx = data
        self.connections[plug_idx] = socket_idx
