from controlpanel.shared.base.button import BaseButton


class DummyButton(BaseButton):
    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)
        self._state: bool = False

    @property
    def state(self) -> int:
        return self._state

    def parse_trigger_data(self, data: bytes) -> tuple[str, bool]:
        print("Parsing Button Data")
        self._state = True if data[0] == 255 else False
        return ("ButtonPressed", self._state) if self._state else ("ButtonReleased", self._state)
