from controlpanel.shared.base import BaseSensor
from typing import Hashable
from abc import abstractmethod
from controlpanel import api


class Sensor(BaseSensor):
    EVENT_TYPES: dict[str, Hashable] = dict()

    @property
    @abstractmethod
    def desynced(self) -> bool:
        pass

    def _fire_event(self, action_name: str, value: Hashable) -> None:
        api.fire_event(self._name, action_name, value)

    @abstractmethod
    def parse_trigger_payload(self, payload: bytes, timestamp: float) -> None:
        pass
