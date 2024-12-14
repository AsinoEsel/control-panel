from ..sensor import Sensor

try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time
    def ticks_ms(): return int(time.time() * 1000)
    def ticks_diff(x, y): return x - y


class BaseRFIDReader(Sensor):
    SUBKEY = 5
    FORGET_TIME = 5000

    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
        self.current_uid: bytearray | None = None
        self.last_scan_time: int = 0

    def get_uid(self) -> None | bytearray:
        raise NotImplementedError("Needs to be implemented by subclass!")

    def get_payload(self) -> bytes:
        return bytes(self.current_uid)

    def update(self):
        uid = self.get_uid()
        if uid is None:
            return
        current_time = ticks_ms()
        if uid == self.current_uid and ticks_diff(current_time, self.last_scan_time) < self.FORGET_TIME:
            return
        self.last_scan_time = current_time
        self.current_uid = uid
        self.callback(uid)
