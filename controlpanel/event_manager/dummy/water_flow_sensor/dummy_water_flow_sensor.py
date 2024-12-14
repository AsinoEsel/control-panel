import struct
from controlpanel.shared.base.water_flow_sensor import BaseWaterFlowSensor


class DummyWaterFlowSensor(BaseWaterFlowSensor):
    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
        self._lifetime_water_flow: int = 0

    def parse_trigger_data(self, data: bytes):
        water_flow = struct.unpack("<d", data)
        self._lifetime_water_flow += water_flow

    @property
    def lifetime_water_flow(self):
        return self._lifetime_water_flow
