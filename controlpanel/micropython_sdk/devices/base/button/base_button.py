from ..sensor import Sensor


class BaseButton(Sensor):
    SUBKEY = 0

    def __init__(self, artnet, name: str, *, callback=None) -> None:
        super().__init__(artnet, name, callback=callback)

    @property
    def state(self) -> int:
        raise NotImplementedError("Needs to be implemented by subclass!")

    def get_payload(self) -> bytes:
        return (self.state * 255).to_bytes(1, "big")
