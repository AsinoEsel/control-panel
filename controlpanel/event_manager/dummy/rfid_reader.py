from controlpanel.shared.base.rfid_reader import BaseRFIDReader
from controlpanel.shared.mixins import DummySensorMixin


class RFIDReader(BaseRFIDReader, DummySensorMixin):
    EVENT_TYPES = {
        "TagScanned": bytearray,
    }

    def __init__(self, artnet, name: str, *, callback=None):
        super().__init__(artnet, name, callback=callback)

    def parse_trigger_payload(self, data: bytes) -> tuple[str: bytearray]:
        self.current_uid = bytearray(data)
        return "TagScanned", self.current_uid
