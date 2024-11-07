import hashlib
from .device import Device


class Fixture(Device):
    def __init__(self, artnet, name: str, *, universe: int | None) -> None:
        super().__init__(artnet, name)
        if universe is None:
            universe = self.calculate_hash()
            # print(f"Auto-assigned universe {universe} to {self.name}.")
        self.universe = universe

    def calculate_hash(self) -> int:
        hash_object = hashlib.sha1(self.name.encode())
        return int.from_bytes(hash_object.digest(), "big") & 0x7FFF

    def send_dmx_data(self):
        self.artnet.send_dmx(self.universe, 0, self.get_dmx_data())

    def get_dmx_data(self) -> bytearray:
        raise NotImplementedError("Needs to be implemented by subclass!")

    def parse_dmx_data(self, data: bytes):
        raise NotImplementedError("Needs to be implemented by subclass!")
