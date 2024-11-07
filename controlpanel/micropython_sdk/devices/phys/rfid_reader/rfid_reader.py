from .mfrc522 import MFRC522
from machine import SoftSPI
from ...base.rfid_reader import BaseRFIDReader
import asyncio


class RFIDReader(BaseRFIDReader, MFRC522):
    def __init__(self, artnet, name: str, spi: SoftSPI, reset: int, chip_select: int, *, callback=None):
        super().__init__(artnet, name, callback=callback)
        MFRC522.__init__(self, spi=spi, gpioRst=reset, gpioCs=chip_select)
                
    def get_uid(self) -> None | bytes:
        (stat, tag_type) = self.request(self.REQIDL)
        if not stat == self.OK:
            return None
        
        (stat, raw_uid) = self.anticoll()
        if not stat == self.OK:
            return None
        
        # print("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
        return raw_uid

    async def run(self, updates_per_second: int):
        sleep_time = 1/updates_per_second
        while True:
            self.update()
            await asyncio.sleep(sleep_time)
