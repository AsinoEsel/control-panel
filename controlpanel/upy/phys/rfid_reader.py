from controlpanel.upy.libs.rfid_reader.mfrc522 import MFRC522
try:
    from typing import Literal
except ImportError:
    Literal = object()
from machine import SPI
from controlpanel.shared.base.rfid_reader import BaseRFIDReader
from .sensor import Sensor
from controlpanel.upy.artnet import ArtNet


class RFIDReader(BaseRFIDReader, Sensor):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 pin_reset: int,
                 pin_chip_select: int,
                 hardware_spi: Literal[1, 2],
                 *,
                 polling_rate_hz: float = 1.0
                 ) -> None:
        Sensor.__init__(self, _artnet, name, polling_rate_hz)
        self._mfrc522 = MFRC522(SPI(hardware_spi, baudrate=1000000), pin_reset, pin_chip_select)
        self._current_uid: bytes | None = None

    def get_uid(self) -> None | bytes:
        (stat, tag_type) = self._mfrc522.request(self._mfrc522.REQIDL)
        if not stat == self._mfrc522.OK:
            return None
        
        (stat, raw_uid) = self._mfrc522.anticoll()
        if not stat == self._mfrc522.OK:
            return None
        
        # print("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
        return raw_uid

    async def poll(self) -> None:
        uid: bytes | None = self.get_uid()
        if uid != self._current_uid:
            self.send_trigger(uid or b"\x00\x00\x00\x00")
