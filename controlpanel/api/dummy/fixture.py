from abc import abstractmethod
from controlpanel.shared.base import BaseFixture


class Fixture(BaseFixture):
    def _send_dmx_data(self, data: bytes | bytearray) -> None:
        self._artnet.send_dmx(self.universe, 0, data)

    @abstractmethod
    def blackout(self) -> None:
        pass

    @abstractmethod
    def whiteout(self) -> None:
        pass
