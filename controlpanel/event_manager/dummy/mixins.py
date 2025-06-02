from typing import Any
from abc import abstractmethod
from typing import Protocol, Hashable
from artnet import ArtNet

class Device(Protocol):
    artnet: ArtNet
    universe: int


class FixtureMixin:
    """A mixin class for Dummy Fixtures"""
    def send_dmx_data(self: "Device", data: bytes | bytearray) -> None:
        self.artnet.send_dmx(self.universe, 0, data)


class SensorMixin:
    """A mixin class for Dummy Sensors"""
    EVENT_TYPES: dict[str: Hashable] = dict()

    @abstractmethod
    def parse_trigger_payload(self: "Device", payload: bytes) -> tuple[str, Any]:
        pass
