from controlpanel.shared.base.button import BaseButton


class DummyButton(BaseButton):
    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)
        self._state = 0

    @property
    def state(self) -> int:
        return self._state

    def parse_trigger_data(self, data: bytes):
        self._state = 1 if data[0] == 255 else 0
