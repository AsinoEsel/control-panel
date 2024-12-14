from ..sensor import Sensor
from controlpanel.shared.subkey_manifest import SubKey


class BaseButton(Sensor):
    SUBKEY = SubKey.PushButton

    def __init__(self, artnet, name: str) -> None:
        super().__init__(artnet, name)

    @property
    def state(self) -> int:
        raise NotImplementedError("Needs to be implemented by subclass!")
