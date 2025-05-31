import struct
from controlpanel.shared.base.banana_plugs import BaseBananaPlugs
from machine import Pin
import asyncio


class BananaPlugs(BaseBananaPlugs):
    def __init__(self, artnet, name: str, plug_pins: list[int], socket_pins: list[int]) -> None:
        super().__init__(artnet, name, len(plug_pins))
        self.plug_pins = [Pin(plug_pin, Pin.OUT) for plug_pin in plug_pins]
        self.socket_pins = [Pin(socket_pin, Pin.IN, Pin.PULL_DOWN) for socket_pin in socket_pins]
        for plug_pin in self.plug_pins:
            plug_pin.value(0)

    def update(self):
        old_connections = self.connections.copy()

        for plug_idx, plug_pin in enumerate(self.plug_pins):
            plug_pin.value(1)
            connection_found = False
            for s, socket_pin in enumerate(self.socket_pins):
                if socket_pin.value() == 1:
                    connection_found = True
                    self.connections[plug_idx] = s
            if not connection_found:
                self.connections[plug_idx] = self.NO_CONNECTION
            plug_pin.value(0)

        for plug_idx in range(len(self.connections)):
            if self.connections[plug_idx] != old_connections[plug_idx]:
                socket_idx = self.connections[plug_idx]
                self.send_trigger_data(struct.pack('BB', plug_idx, socket_idx))

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
