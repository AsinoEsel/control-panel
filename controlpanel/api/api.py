import time
import threading
from typing import TypeVar, TYPE_CHECKING, Optional, Callable, Iterable, Any
from controlpanel.shared.base import Device, Fixture
from controlpanel.event_manager import Event
from itertools import product
from .services import Services
if TYPE_CHECKING:
    from controlpanel.event_manager import EventActionType, EventValueType, CallbackType, SourceNameType


T = TypeVar("T", bound="BaseGame")


def fire_event(source: str = "", action: str = "", value: "EventValueType" = None):
    Services.event_manager.fire_event(Event(source, action, value, None, time.time()))


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


def subscribe(callback: "CallbackType", source_name: Optional["SourceNameType"], event_name: Optional[
    "EventActionType"], condition_value: Optional["EventValueType"], *, fire_once=False, allow_parallelism: bool = False):
    Services.event_manager.subscribe(callback, source_name, event_name, condition_value, fire_once=fire_once, allow_parallelism=allow_parallelism)


def callback(source: str | Iterable[str] | None = None,
             action: str | Iterable[str] | None = None,
             value: Any | Iterable[Any] | None = None, *,
             fire_once: bool = False,
             allow_parallelism: bool = False,
             ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        sources = [source] if isinstance(source, str) or not isinstance(source, Iterable) else source
        actions = [action] if isinstance(action, str) or not isinstance(action, Iterable) else action
        values = [value] if isinstance(value, str) or not isinstance(value, Iterable) else value

        for s, a, v in product(sources, actions, values):
            subscribe(func, s, a, v,
                      fire_once=fire_once,
                      allow_parallelism=allow_parallelism)
        return func

    return decorator


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
