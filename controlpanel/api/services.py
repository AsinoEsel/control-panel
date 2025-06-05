from typing import TYPE_CHECKING, Optional
from controlpanel.dmx import DMXUniverse
import types
from artnet import ArtNet
from .event_manager import EventManager
if TYPE_CHECKING:
    from controlpanel.game_manager import GameManager


class Services:
    """This acts as a simple namespace"""
    artnet: Optional[ArtNet] = None
    event_manager: Optional[EventManager] = None
    game_manager: Optional["GameManager"] = None
    dmx: Optional[DMXUniverse] = None
    loaded_scripts: dict[str, types.ModuleType] = {}
