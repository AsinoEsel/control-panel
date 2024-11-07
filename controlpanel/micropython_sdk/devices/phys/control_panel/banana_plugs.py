from ...base.control_panel.base_banana_plugs import BaseBananaPlugs
from machine import Pin
import asyncio


class BananaPlugs(BaseBananaPlugs):
    def __init__(self, artnet, name: str, plug_pins: list[int], socket_pins: list[int], *, callback=None) -> None:
        super().__init__(artnet, name, callback=callback)
        self.plug_pins = [Pin(plug_pin, Pin.OUT) for plug_pin in plug_pins]
        self.socket_pins = [Pin(socket_pin, Pin.IN, Pin.PULL_DOWN) for socket_pin in socket_pins]
        self.connections = [None for _ in self.plug_pins]
        for plug_pin in self.plug_pins:
            plug_pin.value(0)
    
    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            old_connections = self.connections.copy()
            
            for p, plug_pin in enumerate(self.plug_pins):
                plug_pin.value(1)
                connection_found = False
                for s, socket_pin in enumerate(self.socket_pins):
                    if socket_pin.value() == 1:
                        connection_found = True
                        self.connections[p] = s
                if not connection_found:
                    self.connections[p] = None                
                plug_pin.value(0)
                        
            for p in range(len(self.connections)):
                if self.connections[p] != old_connections[p]:
                    self.callback(p, self.connections[p])                        
            
            await asyncio.sleep_ms(sleep_time_ms)
