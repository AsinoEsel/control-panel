try:
    from typing import Any
    from abc import abstractmethod
    from typing import Protocol, Hashable
    from artnet import ArtNet

    class Device(Protocol):
        artnet: ArtNet
        name: str
except ImportError:
    Any = object()
    Hashable = Any


class PhysFixtureMixin:
    """A mixin class for Phys Fixtures"""
    @abstractmethod
    def parse_dmx(self: "Device", packet: bytes) -> None:
        # Decode and apply DMX data
        pass


class DummyFixtureMixin:
    """A mixin class for Dummy Fixtures"""
    @abstractmethod
    def send_dmx_data(self: "Device", data: bytes | bytearray) -> None:
        # Encode and send DMX packet
        pass


class PhysSensorMixin:
    """A mixin class for Phys Sensors"""
    def send_trigger(self: "Device", payload: bytes) -> None:
        data = self.name.encode('ascii') + b'\x00' + payload
        self.artnet.send_trigger(key=76, subkey=0, data=data)


class DummySensorMixin:
    EVENT_TYPES: dict[str: Hashable] = dict()

    """A mixin class for Dummy Sensors"""
    @abstractmethod
    def parse_trigger_payload(self: "Device", payload: bytes) -> tuple[str, Any]:
        pass
