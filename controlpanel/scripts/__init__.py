"""
This package contains all script files for handling game logic.
Each script file is meant to work independent of the others.
The scripts are run on execution of the "load_scripts" function in this package.
"""

import time
import threading
from artnet import ArtNet
from controlpanel.dmx import DMXUniverse
from controlpanel.event_manager import EventManager, EventNameType, EventValueType, Event, Subscriber, CallbackType, SourceNameType
from controlpanel.gui.window_manager import WindowManager
import os
import glob
import importlib
from functools import wraps
import inspect
from controlpanel.micropython_sdk.device_manifest import DeviceManifestType  # TODO: Fix console clutter coming from here


class ControlAPI:
    artnet: ArtNet = None
    event_manager: EventManager = None
    devices: DeviceManifestType = None
    window_manager: WindowManager = None
    dmx: DMXUniverse = None

    @classmethod
    def fire_event(cls, source: str, name: str, value: EventValueType = None):
        cls.event_manager.fire_event(Event(source, name, value, None, time.time()))

    @staticmethod
    def call_with_frequency(frequency: float | int):
        def decorator(func):
            def wrapper(*args, **kwargs):
                def run_function():
                    interval = 1 / frequency  # Calculate interval based on frequency
                    while True:
                        func(*args, **kwargs)
                        time.sleep(interval)  # Wait for the calculated interval

                thread = threading.Thread(target=run_function, daemon=True)
                thread.start()

            wrapper()  # Automatically start the function without needing to call it
            return wrapper

        return decorator

    @classmethod
    def subscribe(cls, callback: CallbackType, source_name: SourceNameType | None, event_name: EventNameType | None, condition_value: EventValueType | None, *, fire_once=False, allow_parallelism: bool=False):
        cls.event_manager.subscribe(callback, source_name, event_name, condition_value, fire_once=fire_once, allow_parallelism=allow_parallelism)

    @classmethod
    def callback(cls, source_name: SourceNameType | None, event_name: EventNameType | None, condition_value: EventValueType = None, *, fire_once=False, allow_parallelism: bool=False):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            # Register the function as a callback with the event manager
            cls.event_manager.subscribe(func, source_name, event_name, condition_value, fire_once=fire_once, allow_parallelism=allow_parallelism)

            return wrapper

        return decorator

    @staticmethod
    def run_once_on_setup(func):
        """Decorator to mark functions to be run once during setup."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._run_once_on_setup = True  # Add a custom attribute to mark the function
        return wrapper


def load_scripts(args: list[str]):
    if not args:
        module_dir = os.path.dirname(__file__)
        py_files = glob.glob(os.path.join(module_dir, "*.py"))
        scripts_to_load = [os.path.basename(f) for f in py_files if not f.endswith('__init__.py')]
    else:
        scripts_to_load: list[str] = []
        while not scripts_to_load or args:
            for arg in args:
                if not arg.endswith(".py") and not arg.endswith(".txt"):
                    if os.path.exists(os.path.join(os.path.dirname(__file__), arg + ".py")):
                        args.append(arg + ".py")
                        args.remove(arg)
                        continue
                    if os.path.exists(os.path.join(os.path.dirname(__file__), arg + ".txt")):
                        args.append(arg + ".txt")
                        args.remove(arg)
                        continue
                    raise FileNotFoundError(f"Could not find a file matching {arg}.")
                if arg.endswith(".txt") and not os.path.exists(os.path.join(os.path.dirname(__file__), arg)):
                    raise FileNotFoundError(f"The script preset file {arg} could not be found.")
                if arg.endswith(".py") and not os.path.exists(os.path.join(os.path.dirname(__file__), arg)):
                    raise FileNotFoundError(f"The script file {arg} could not be found.")
                if arg.endswith(".txt"):
                    with open(os.path.join(os.path.dirname(__file__), arg), "r") as f:
                        entries = f.readlines()
                    for entry in entries:
                        entry = entry.strip()
                        if entry:
                            args.append(entry)
                    args.remove(arg)
                    continue
                if arg not in scripts_to_load:
                    scripts_to_load.append(arg)
                    args.remove(arg)
                    continue
                else:
                    args.remove(arg)
                    continue

    print("Loading the following scripts:")
    for script in scripts_to_load:
        print(f"- {script}")

    for script in scripts_to_load:
        script = script.removesuffix(".py")
        module = importlib.import_module(f".{script}", package=__name__)
        # Inspect the module for all functions
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            # Check if the function has been decorated with 'run_once_on_setup'
            if getattr(obj, "_run_once_on_setup", False):
                obj()  # Call the decorated function
