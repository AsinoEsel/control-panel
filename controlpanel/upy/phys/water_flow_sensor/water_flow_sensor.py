from machine import Pin
import struct
from controlpanel.shared.base.water_sensor import BaseWaterSensor
import asyncio


class WaterFlowSensor(BaseWaterSensor):
    def __init__(self, artnet, name: str, pin: int) -> None:
        super().__init__(artnet, name)
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_RISING, handler=self.water_flow_irq_handler)
        self.flow_counter = 0

    def water_flow_irq_handler(self, pin: Pin):
        self.flow_counter += 1

    def update(self):
        print(self.flow_counter)
        if self.flow_counter > 0:
            self.send_trigger_data(struct.pack("<l", int(self.flow_counter * self.CORRECTION_FACTOR)))
            self.flow_counter = 0

    async def run(self, updates_per_second: float):
        sleep_time = 1 / updates_per_second
        while True:
            self.update()
            await asyncio.sleep(sleep_time)
