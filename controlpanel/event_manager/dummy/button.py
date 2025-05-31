from controlpanel.shared.base.button import BaseButton
from controlpanel.shared.mixins import DummySensorMixin


class Button(BaseButton, DummySensorMixin):
    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)
        self._state: bool = False

    @property
    def state(self) -> int:
        return self._state

    def parse_trigger(self, data: bytes) -> tuple[str, bool]:
        assert len(data) == 1, "Data is of unexpected length"
        self._state = bool(data[0])
        return ("ButtonPressed", self._state) if self._state else ("ButtonReleased", self._state)
