from controlpanel.shared.base.rotary_dial import BaseRotaryDial
import time


class DummyRotaryDial(BaseRotaryDial):
    def __init__(self, artnet, name: str):
        super().__init__(artnet, name)
        self.last_entered_number: int | None = None
        self.last_entered_number_timestamp: float | None = None

    def parse_trigger_data(self, data: bytes) -> tuple[str, int]:
        self.last_entered_number = data[0]
        self.last_entered_number_timestamp = time.time()
        digit = (data[0]) % 10
        return "Digit", digit
