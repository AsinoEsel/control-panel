import struct
from controlpanel.shared.base.banana_plugs import BaseBananaPlugs
from controlpanel.upy.phys import Sensor
from machine import Pin, SoftSPI, I2C
from controlpanel.upy.artnet import ArtNet


class BananaPlugs(BaseBananaPlugs, Sensor):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 plug_pins: list[int],
                 socket_pins: list[int],
                 *,
                 polling_rate_hz: float = BaseBananaPlugs.DEFAULT_POLLING_RATE_HZ,
                 ) -> None:
        super().__init__(len(plug_pins))
        Sensor.__init__(self, _context[0], _name, polling_rate_hz)
        self.plug_pins = [Pin(plug_pin, Pin.OUT) for plug_pin in plug_pins]
        self.socket_pins = [Pin(socket_pin, Pin.IN, Pin.PULL_DOWN) for socket_pin in socket_pins]
        for plug_pin in self.plug_pins:
            plug_pin.value(0)

    def _get_high_socket_idx(self) -> int:
        """Returns the first socket idx that is currently high, otherwise returns self.NO_CONNECTION"""
        for socket_idx, socket_pin in enumerate(self.socket_pins):
            if socket_pin.value() == 1:
                return socket_idx
        return self.NO_CONNECTION

    def find_connected_socket_idx(self, plug_pin: Pin) -> int:
        plug_pin.value(1)
        connected_socket = self._get_high_socket_idx()
        plug_pin.value(0)
        return connected_socket

    async def update(self) -> None:
        new_connections: list[tuple[int, int]] = []

        # Find new connections
        for plug_idx, plug_pin in enumerate(self.plug_pins):
            connected_socket_idx = self.find_connected_socket_idx(plug_pin)
            if connected_socket_idx != self._connections[plug_idx]:
                self._connections[plug_idx] = connected_socket_idx
                new_connections.append((plug_idx, connected_socket_idx))

        for plug_idx, socket_idx in new_connections:
            self._send_trigger_packet(struct.pack('BB', plug_idx, socket_idx))
