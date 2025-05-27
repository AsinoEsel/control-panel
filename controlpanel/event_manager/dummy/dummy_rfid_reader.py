from controlpanel.shared.base.rfid_reader import BaseRFIDReader


class DummyRFIDReader(BaseRFIDReader):
    def __init__(self, artnet, name: str, *, callback=None):
        super().__init__(artnet, name, callback=callback)

    def parse_trigger_data(self, data: bytes):
        self.current_uid = bytearray(data)
        print(f"set current uid to {self.current_uid}")
