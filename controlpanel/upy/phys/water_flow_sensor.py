from machine import Pin
import struct
from controlpanel.upy.artnet import ArtNet
from controlpanel.shared.base.water_flow_sensor import BaseWaterFlowSensor
from controlpanel.upy.phys import Sensor


class WaterFlowSensor(BaseWaterFlowSensor, Sensor):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 pin: int,
                 *,
                 polling_rate_hz: float = BaseWaterFlowSensor.DEFAULT_POLLING_RATE_HZ
                 ) -> None:
        Sensor.__init__(self, _artnet, name, polling_rate_hz)
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._pin.irq(trigger=Pin.IRQ_RISING, handler=self.water_flow_irq_handler)  # correct edge?
        self._flow_counter: int = 0

    def water_flow_irq_handler(self, pin: Pin):
        self._flow_counter += 1  # can technically overflow (ha) if the counter hits 2^32 but who cares

    async def poll(self) -> None:
        if not self._flow_counter:
            return
        self.send_trigger(struct.pack("<I", self._flow_counter))
        self._flow_counter = 0
