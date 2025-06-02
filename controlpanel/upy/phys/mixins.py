try:
    from abc import abstractmethod
    from typing import Protocol
    from artnet import ArtNet

    class Device(Protocol):
        artnet: ArtNet
        name: str
except ImportError:
    abstractmethod = lambda func: func


class FixtureMixin:
    """A mixin class for Phys Fixtures"""
    @abstractmethod
    def parse_dmx_data(self: "Device", data: bytes) -> None:
        # Decode and apply DMX data
        pass


class SensorMixin:
    """A mixin class for Phys Sensors"""
    def send_trigger(self: "Device", payload: bytes) -> None:
        data = self.name.encode('ascii') + b'\x00' + payload
        self.artnet.send_trigger(key=76, subkey=0, data=data)
