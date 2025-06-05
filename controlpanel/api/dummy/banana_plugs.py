from controlpanel.shared.base.banana_plugs import BaseBananaPlugs
from .sensor import Sensor


class BananaPlugs(BaseBananaPlugs, Sensor):
    EVENT_TYPES = {
        "PlugDisconnected": tuple[int, None],
        "PlugConnected": tuple[int, int],
    }

    def __init__(self, _artnet, name: str, plug_pins: list[int]):
        super().__init__(len(plug_pins))
        Sensor.__init__(self, _artnet, name)

    @property
    def connections(self) -> tuple[int | None, ...]:
        return tuple(socket_idx if socket_idx != self.NO_CONNECTION else None for socket_idx in self._connections)

    def parse_trigger_payload(self, data: bytes) -> tuple[str, tuple[int, int | None]]:
        assert len(data) == 2, "Data is of unexpected length"
        plug_idx, socket_idx = data
        self._connections[plug_idx] = socket_idx
        if socket_idx == self.NO_CONNECTION:
            return "PlugDisconnected", (plug_idx, None)
        else:
            return "PlugConnected", (plug_idx, socket_idx)
