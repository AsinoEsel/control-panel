from controlpanel.shared.base import Device, BaseSensor
from controlpanel.shared.compatibility import abstractmethod
from controlpanel.upy.artnet import ArtNet


class Sensor(BaseSensor):
    def __init__(self, _artnet: ArtNet, name: str, polling_rate_hz: float = 1.0):
        super().__init__(_artnet, name)
        self.polling_rate_ms: int = int(1000 / polling_rate_hz) if polling_rate_hz > 0.0 else 0

    @abstractmethod
    async def poll(self) -> None:
        pass

    def send_trigger(self: Device, payload: bytes | bytearray) -> None:
        data = self.name.encode('ascii') + b'\x00' + payload
        self._artnet.send_trigger(key=76, subkey=0, data=data)
