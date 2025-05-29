from typing import Literal
from controlpanel.event_manager.device_getter import get_device
from controlpanel.event_manager import Event
from .services import Services
from .load_scripts import load_scripts
from .api import callback, call_with_frequency, fire_event


def __getattr__(name: Literal["artnet", "event_manager", "game_manager", "dmx"]):
    if name == "artnet":
        return Services.artnet
    elif name == "event_manager":
        return Services.event_manager
    elif name == "game_manager":
        return Services.game_manager
    elif name == "dmx":
        return Services.dmx
    elif name == "loaded_scripts":
        return Services.loaded_scripts
    elif name == "add_game":
        return Services.game_manager.add_game
    elif name == "get_game":
        return Services.game_manager.get_game
    raise AttributeError(f"module has no attribute {name}")
