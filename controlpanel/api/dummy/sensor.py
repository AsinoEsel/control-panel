from controlpanel.shared.base import Device, BaseSensor
from typing import Hashable, Any
from abc import abstractmethod


class Sensor(BaseSensor):
    EVENT_TYPES: dict[str: Hashable] = dict()

    @abstractmethod
    def parse_trigger_payload(self: "Device", payload: bytes) -> tuple[str, Any]:
        pass
