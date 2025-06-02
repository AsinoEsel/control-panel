import time
import threading
from typing import TypeVar, TYPE_CHECKING, Optional
from controlpanel.shared.base import Device, Fixture
from .services import Services
if TYPE_CHECKING:
    from controlpanel.event_manager import EventSourceType, EventActionType, EventValueType, CallbackType


T = TypeVar("T", bound="BaseGame")


def fire_event(source: "EventSourceType",
               action: "EventActionType",
               value: "EventValueType", *,
               sender: tuple[str, int] | None = None,
               ts: float | None = None) -> None:
    Services.event_manager.fire_event(source, action, value, sender=sender, ts=ts)


def call_with_frequency(frequency: float | int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def run_function():
                interval = 1 / frequency  # Calculate interval based on frequency
                setattr(wrapper, "_is_running", True)
                setattr(wrapper, "stop", lambda: setattr(wrapper, "_is_running", False))
                while getattr(wrapper, "_is_running"):
                    func(*args, **kwargs)
                    time.sleep(interval)  # Wait for the calculated interval

            thread = threading.Thread(target=run_function, daemon=True)
            thread.start()

        wrapper()  # Automatically start the function without needing to call it
        return wrapper

    return decorator


def subscribe(callback: "CallbackType", source_name: Optional["EventSourceType"], action: Optional[
    "EventActionType"], condition_value: Optional["EventValueType"], *, fire_once=False, allow_parallelism: bool = False):
    Services.event_manager.subscribe(callback, source_name, action, condition_value, fire_once=fire_once, allow_parallelism=allow_parallelism)


def send_dmx(device_name: str, data: bytes):
    device: Device = Services.event_manager.devices.get(device_name)
    if device is None:
        print("No device with that name exists in the Device Manifest.")
        return
    if not isinstance(device, Fixture):
        print("Device {device_name} is not a Fixture and hence does not receive DMX signals.")
        return
    universe = device.universe
    print(f"Sending DMX Package to {device_name} @ {universe} with data {data}")
    Services.artnet.send_dmx(universe, 0, bytearray(data))
