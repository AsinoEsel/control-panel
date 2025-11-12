from artnet import ArtNet
from .sensor import Sensor
import time
from controlpanel import api


class RotaryDial(Sensor):
    EVENT_TYPES = {
        "DigitEntered": int,
        "SequenceEntered": tuple[int, ...],
    }

    def __init__(self, _artnet: ArtNet, _name: str, /, *, confirmation_time_seconds: float = 3.0, max_digits: int = 8):
        super().__init__(_artnet, _name)
        self._last_digit: int | None = None
        self._last_update: float = 0.0
        self._confirmation_time_seconds: float = confirmation_time_seconds
        self._max_digits: int = max_digits
        self._entered_sequence: list[int] = []
        api.subscribe(callback=self._wait_for_confirmation,
                      source_name=_name,
                      action="DigitEntered",
                      condition_value=None,
                      allow_parallelism=True)

    @property
    def desynced(self):
        raise NotImplementedError

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        digit: int = (data[0]) % 10
        self._last_digit = digit
        self._entered_sequence.append(digit)
        self._last_update = time.time()
        self._fire_event("DigitEntered", digit)

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
