"""
This package contains all script files for handling game logic.
Each script file is meant to work independent of the others.
The scripts are run on execution of the "load_scripts" function in this package.
"""

import time
import threading
import types
from typing import TypeVar, TYPE_CHECKING, Optional
from controlpanel.dmx import DMXUniverse
from controlpanel.game_manager import GameManager, BaseGame
from controlpanel.shared.base import Device, Fixture
import os
import sys
import importlib
from functools import wraps
from controlpanel.event_manager import Event
if TYPE_CHECKING:
    from controlpanel.shared.device_manifest import DeviceManifestType
    from controlpanel.event_manager import EventManager, EventNameType, EventValueType, Event, CallbackType, SourceNameType
    from artnet import ArtNet


T = TypeVar("T", bound="BaseGame")


class ControlAPI:
    artnet: "ArtNet" = None
    event_manager: "EventManager" = None
    devices: "DeviceManifestType" = None
    game_manager: GameManager = None
    dmx: DMXUniverse = None
    loaded_scripts: dict[str, types.ModuleType] = {}

    @classmethod
    def add_game(cls, game: T, *, make_current: bool = False) -> T:
        if cls.game_manager is None:
            raise NotImplementedError
        else:
            return cls.game_manager.add_game(game, make_current)

    @classmethod
    def get_game(cls, name: str | None = None) -> BaseGame | None:
        return cls.game_manager.get_game(name)

    @classmethod
    def fire_event(cls, source: str = "", name: str = "", value: "EventValueType" = None):
        cls.event_manager.fire_event(Event(source, name, value, None, time.time()))

    @staticmethod
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

    @classmethod
    def subscribe(cls, callback: "CallbackType", source_name: Optional["SourceNameType"], event_name: Optional["EventNameType"], condition_value: Optional["EventValueType"], *, fire_once=False, allow_parallelism: bool = False):
        cls.event_manager.subscribe(callback, source_name, event_name, condition_value, fire_once=fire_once, allow_parallelism=allow_parallelism)

    @classmethod
    def callback(cls, source_name: Optional["SourceNameType"] = None, event_name: Optional["EventNameType"] = None, condition_value: Optional["EventValueType"] = None, *, fire_once=False, allow_parallelism: bool = False):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            # Register the function as a callback with the event manager
            cls.event_manager.subscribe(func, source_name, event_name, condition_value, fire_once=fire_once, allow_parallelism=allow_parallelism)

            return wrapper

        return decorator

    @classmethod
    def send_dmx(cls, device_name: str, data: bytes):
        device: Device = cls.devices.get(device_name)
        if device is None:
            print("No device with that name exists in the Device Manifest.")
            return
        if not isinstance(device, Fixture):
            print("Device {device_name} is not a Fixture and hence does not receive DMX signals.")
            return
        universe = device.universe
        print(f"Sending DMX Package to {device_name} @ {universe} with data {data}")
        cls.artnet.send_dmx(universe, 0, bytearray(data))


def load_scripts(args: list[str]) -> None:
    """
    This is where we load our "user scripts" on boot, by taking in a list of script file names, and then importing them.
    """

    # First, we "unpack" all .txt files
    while any(arg.endswith(".txt") for arg in args):
        for arg in args:
            if arg.endswith(".txt"):
                with open(os.path.join(os.path.dirname(__file__), arg), "r") as f:
                    entries = f.readlines()
                for entry in entries:
                    entry = entry.strip()
                    if entry:
                        args.append(entry)
                args.remove(arg)
                break

    failed: list[tuple[str, Exception]] = []
    success: list[tuple[str, set[str]]] = []
    for arg in args:
        if arg.endswith(".py"):
            arg = arg.removesuffix(".py")
        try:
            original_modules = set(sys.modules.keys())
            imported_module = importlib.import_module(f".{arg}", package=__name__)
            ControlAPI.loaded_scripts[arg] = imported_module
            new_modules = set(sys.modules.keys()) - original_modules
            if not new_modules:
                continue  # Skip this module because it has apparently already been imported before as a dependency
            dependencies = set()
            for new_module in new_modules:
                if not new_module.startswith("controlpanel.scripts."):  # are only interested in our scripts
                    continue
                new_module_name = new_module.removeprefix("controlpanel.scripts.")
                script_name, *submodules = new_module_name.split(".", maxsplit=1)
                if arg == script_name:  # Don't count imported module as dependency of itself
                    continue
                dependencies.add(script_name)
                if not submodules:
                    ControlAPI.loaded_scripts[script_name] = sys.modules.get(new_module)

            success.append((arg, dependencies))
        except (ModuleNotFoundError, ImportError) as e:
            raise
            failed.append((arg, e))

    if success:
        print("Successfully loaded the following scripts:")
        for script, dependencies in success:
            print(f"- {script}")
            for dependency in dependencies:
                print(f"- {dependency:<15} (dependency of {script})")

    if failed:
        print("Failed to load the following scripts:")
        for script, error in failed:
            print(f"- {script} ({error.__class__.__name__}: {str(error)})")
