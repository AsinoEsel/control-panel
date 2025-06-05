import struct
from controlpanel.shared.base.water_flow_sensor import BaseWaterFlowSensor
from .sensor import Sensor
from artnet import ArtNet


class WaterFlowSensor(BaseWaterFlowSensor, Sensor):
    EVENT_TYPES = {
        "WaterFlow": int,
    }

    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 *,
                 polling_rate_hz: float = BaseWaterFlowSensor.DEFAULT_POLLING_RATE_HZ,
                 ) -> None:
        super().__init__(polling_rate_hz)
        Sensor.__init__(self, _artnet, name)
        self._lifetime_water_flow: int = 0
        self._water_flow_rate: float = 0.0

    @property
    def lifetime_water_flow(self):
        return self._lifetime_water_flow

    @property
    def water_flow_rate(self):
        return self._water_flow_rate

    def parse_trigger_payload(self, data: bytes) -> tuple[str, int]:
        water_flow: int = struct.unpack("<I", data)[0]
        self._lifetime_water_flow += water_flow
        self._water_flow_rate = water_flow / self._polling_time_seconds
        return "WaterFlow", water_flow
