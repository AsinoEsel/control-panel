from ...base.sensor import Sensor


class BaseBananaPlugs(Sensor):
    def __init__(self, artnet, name: str, *, callback=None):
        super().__init__(artnet, name, callback=callback)
        self.connections: list[int] = []

    def get_payload(self) -> bytes:
        raise NotImplementedError("TODO")
