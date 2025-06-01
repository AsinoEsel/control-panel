from controlpanel.shared.base import Device
from .services import Services


def get_device(device_name) -> Device:
    return Services.event_manager.devices.get(device_name)
