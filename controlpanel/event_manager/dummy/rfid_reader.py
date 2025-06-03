from controlpanel.shared.base.rfid_reader import BaseRFIDReader
from controlpanel.event_manager.dummy import SensorMixin


class RFIDReader(BaseRFIDReader, SensorMixin):
    EVENT_TYPES = {
        "TagScanned": bytearray | bytes,
    }

    def __init__(self, artnet, name: str, *, callback=None):
        super().__init__(artnet, name, callback=callback)

    def parse_trigger_payload(self, data: bytes) -> tuple[str: bytearray]:
        self.current_uid = bytearray(data)
        return "TagScanned", self.current_uid
