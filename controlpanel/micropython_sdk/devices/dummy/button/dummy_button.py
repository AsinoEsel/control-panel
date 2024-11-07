from ...base.button import BaseButton


class DummyButton(BaseButton):
    def __init__(self, artnet, name: str, *, callback=None) -> None:
        super().__init__(artnet, name, callback=callback)
        self._state = 0

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, val):
        if val != self.state:
            self._state = val
            self.callback(self.state)

    def parse_trigger_data(self, data: bytes):
        self._state = 1 if data[0] == 255 else 0
        print(f"set state to {self._state}")
