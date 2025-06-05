from controlpanel.shared.base.rfid_reader import BaseRFIDReader
from .sensor import Sensor
from controlpanel import api


class RFIDReader(BaseRFIDReader, Sensor):
    EVENT_TYPES = {
        "TagScanned": bytearray | bytes,
        "TagRemoved": None,
    }

    def __init__(self, _artnet, name: str):
        Sensor.__init__(self, _artnet, name)
        self._current_uid: bytes | None = None

    @property
    def current_uid(self) -> bytes | None:
        return self._current_uid

    def parse_trigger_payload(self, data: bytes) -> tuple[str: bytearray]:
        previous_uid = self._current_uid
        new_uid = data if data else None
        self._current_uid = new_uid
        if new_uid and not previous_uid:
            return "TagScanned", new_uid
        if not new_uid and previous_uid:
            return "TagRemoved", previous_uid
        api.fire_event(self.name, "TagRemoved", previous_uid)
        return "TagScanned", new_uid
