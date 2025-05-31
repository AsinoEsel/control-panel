import struct
from controlpanel.shared.base.water_sensor import BaseWaterSensor


class WaterSensor(BaseWaterSensor):
    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
        self._lifetime_water_flow: int = 0

    @property
    def lifetime_water_flow(self):
        return self._lifetime_water_flow

    def parse_trigger_data(self, data: bytes) -> tuple[str, int]:
        water_flow: int = struct.unpack("<l", data)[0]
        self._lifetime_water_flow += water_flow
        return "WaterFlow", water_flow
