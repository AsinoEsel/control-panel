from controlpanel.shared.base.button import BaseButton
from artnet import ArtNet
from .sensor import Sensor


class Button(BaseButton, Sensor):
    EVENT_TYPES = {
        "ButtonPressed": bool,
        "ButtonReleased": bool,
    }

    def __init__(self, _artnet: ArtNet, name: str):
        Sensor.__init__(self, _artnet, name)
        self._state: bool = False

    def __bool__(self) -> bool:
        return self._state

    def get_pressed(self) -> bool:
        return self._state

    def parse_trigger_payload(self, data: bytes) -> tuple[str, bool]:
        assert len(data) == 1, "Data is of unexpected length"
        is_pressed: bool = bool(data[0])
        self._state = is_pressed
        if self._state:
            return "ButtonPressed", is_pressed
        else:
            return "ButtonReleased", is_pressed
