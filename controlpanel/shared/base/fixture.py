import hashlib
from .device import Device


class Fixture(Device):
    def __init__(self, artnet, name: str, *, universe: int | None) -> None:
        super().__init__(artnet, name)
        self.universe = self._calculate_hash(name) if universe is None else universe

    @staticmethod
    def _calculate_hash(string: str) -> int:
        hash_object = hashlib.sha1(string.encode())
        return int.from_bytes(hash_object.digest(), "big") & 0x7FFF

    def blackout(self) -> None:
        pass
