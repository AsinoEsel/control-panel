import struct
from controlpanel.shared.base.water_flow_sensor import BaseWaterFlowSensor
from controlpanel.shared.mixins import DummySensorMixin


class WaterFlowSensor(BaseWaterFlowSensor, DummySensorMixin):
    EVENT_TYPES = {
        "WaterFlow": int,
    }

    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
        self._lifetime_water_flow: int = 0

    @property
    def lifetime_water_flow(self):
        return self._lifetime_water_flow

    def parse_trigger_payload(self, data: bytes) -> tuple[str, int]:
        water_flow: int = struct.unpack("<l", data)[0]
        self._lifetime_water_flow += water_flow
        return "WaterFlow", water_flow
