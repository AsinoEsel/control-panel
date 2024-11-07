from ..sensor import Sensor


class BaseRotaryDial(Sensor):
    SUBKEY = 7
    CONFIRMATION_TIME = 3000

    def __init__(self, artnet, name: str, *, callback=None):
        super().__init__(artnet, name, callback=callback)
        self.count: int = 0
        self.entered_numbers: list[int] = []
        self.confirmed_numbers: list[int] = []

    def update(self):
        raise NotImplementedError("Needs to be implemented by subclass!")

    def get_payload(self) -> bytes:
        return bytes(self.confirmed_numbers)
    