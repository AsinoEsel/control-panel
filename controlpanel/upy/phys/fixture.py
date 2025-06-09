from controlpanel.shared.base import Device, BaseFixture
from controlpanel.shared.compatibility import abstractmethod


class Fixture(BaseFixture):
    @abstractmethod
    async def update(self) -> None:
        pass

    @abstractmethod
    def parse_dmx_data(self: Device, data: bytes) -> None:
        """Decode and apply DMX data"""
        pass
