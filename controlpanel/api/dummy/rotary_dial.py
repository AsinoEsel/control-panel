from artnet import ArtNet
from controlpanel.shared.base.rotary_dial import BaseRotaryDial
from .sensor import Sensor
import time
from controlpanel import api


class RotaryDial(BaseRotaryDial, Sensor):
    EVENT_TYPES = {
        "DigitEntered": int,
        "SequenceEntered": tuple[int, ...],
    }

    def __init__(self, _artnet: ArtNet, name: str, *, confirmation_time_seconds: float = 3.0, max_digits: int = 8):
        Sensor.__init__(self, _artnet, name)
        self._last_digit: int | None = None
        self._last_update: float = 0.0
        self._confirmation_time_seconds: float = confirmation_time_seconds
        self._max_digits: int = max_digits
        self._entered_sequence: list[int] = []
        api.subscribe(callback=self._wait_for_confirmation,
                      source_name=name,
                      action="DigitEntered",
                      condition_value=None,
                      allow_parallelism=True)

    def parse_trigger_payload(self, data: bytes) -> tuple[str, int]:
        digit: int = (data[0]) % 10
        self._last_digit = digit
        self._entered_sequence.append(digit)
        self._last_update = time.time()
        return "DigitEntered", digit

    def _wait_for_confirmation(self, event: api.Event) -> None:
        time.sleep(self._confirmation_time_seconds)
        if time.time() - self._last_update > self._confirmation_time_seconds:
            self._confirm_sequence()

    def _confirm_sequence(self):
        entered_sequence: tuple[int, ...] = self.get_entered_sequence()
        api.fire_event(self.name, "SequenceEntered", entered_sequence)
        self._entered_sequence.clear()

    def get_last_entered_digit(self) -> int | None:
        return self._last_digit

    def get_entered_sequence(self) -> tuple[int, ...]:
        return tuple(self._entered_sequence)