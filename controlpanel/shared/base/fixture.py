from .device import Device
from controlpanel.shared.compatibility import abstractmethod


class BaseFixture(Device):
    def __init__(self, _artnet, name: str, update_rate_hz: float = 1.0, *, universe: int | None) -> None:
        super().__init__(_artnet, name)
        self.update_rate_ms: int = int(1000 / update_rate_hz) if update_rate_hz > 0.0 else 0
        self._universe = self._universe_from_string(name) if universe is None else universe

    @property
    def universe(self) -> int:
        return self._universe

    @staticmethod
    def _universe_from_string(string: str) -> int:
        import hashlib
        hash_object = hashlib.sha1(string.encode())
        return int.from_bytes(hash_object.digest(), "big") & 0x7FFF  # max 32767 universes (15bit)

    @abstractmethod
    async def update(self) -> None:
        pass
