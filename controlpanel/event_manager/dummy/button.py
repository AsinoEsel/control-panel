from controlpanel.shared.base.button import BaseButton
from controlpanel.event_manager.dummy import SensorMixin


class Button(BaseButton, SensorMixin):
    EVENT_TYPES = {
        "ButtonPressed": bool,
        "ButtonReleased": bool,
    }

    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)
        self._state: bool = False

    @property
    def state(self) -> int:
        return self._state

    def parse_trigger_payload(self, data: bytes) -> tuple[str, bool]:
        assert len(data) == 1, "Data is of unexpected length"
        self._state = bool(data[0])
        if self._state:
            return "ButtonPressed", self._state
        else:
            return "ButtonReleased", self._state
