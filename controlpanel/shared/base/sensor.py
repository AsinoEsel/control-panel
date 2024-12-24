from .device import Device
from controlpanel.shared.subkey_manifest import KEY_CONTROL_PANEL_PROTOCOL, SubKey
try:
    from typing import Any
except ImportError:
    Any = object


class Sensor(Device):
    SUBKEY = SubKey.Any

    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)

    def send_trigger_data(self, payload: bytes):
        data = self.name.encode('ascii') + b'\x00' + payload
        print(f"Sending Trigger with subkey {self.SUBKEY} and data {data}")
        self.artnet.send_trigger(key=KEY_CONTROL_PANEL_PROTOCOL, subkey=self.SUBKEY, data=data)

    def get_payload(self) -> bytes:
        return b""

    def parse_trigger_data(self, data: bytes) -> tuple[str, Any]:
        pass
