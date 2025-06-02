from controlpanel.shared.base.banana_plugs import BaseBananaPlugs
from controlpanel.shared.mixins import DummySensorMixin


class BananaPlugs(BaseBananaPlugs, DummySensorMixin):
    EVENT_TYPES = {
        "PlugDisconnected": tuple[int, None],
        "PlugConnected": tuple[int, int],
    }

    def __init__(self, artnet, name: str, plug_count: int):
        super().__init__(artnet, name, plug_count)

    def parse_trigger_payload(self, data: bytes) -> tuple[str, tuple[int, int | None]]:
        assert len(data) == 2
        plug_idx, socket_idx = data
        self.connections[plug_idx] = socket_idx
        if socket_idx == self.NO_CONNECTION:
            return "PlugDisconnected", (plug_idx, None)
        else:
            return "PlugConnected", (plug_idx, socket_idx)
