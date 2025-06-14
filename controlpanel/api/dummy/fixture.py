import asyncio
from abc import abstractmethod
from controlpanel.shared.base import BaseFixture


class Fixture(BaseFixture):
    def __init__(self, _artnet, name: str, *, universe: int | None, correction_rate_hz: float | None) -> None:
        super().__init__(_artnet, name, universe=universe)
        self._correction_rate_hz: float = correction_rate_hz if correction_rate_hz is not None else 1.0
        self._seq: int = 1

    def _send_dmx_packet(self, data: bytes | bytearray) -> None:
        self._artnet.send_dmx(self.universe, self._seq, data)
        self._increment_seq()

    async def send_dmx_loop(self) -> None:
        while True:
            self.send_dmx()
            await asyncio.sleep(1 / self._correction_rate_hz)

    @abstractmethod
    def send_dmx(self) -> None:
        pass

    @abstractmethod
    def blackout(self) -> None:
        pass

    @abstractmethod
    def whiteout(self) -> None:
        pass
