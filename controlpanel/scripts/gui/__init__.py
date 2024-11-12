from .window_manager import WindowManager
from controlpanel.scripts import ControlAPI

window_manager = WindowManager()
ControlAPI.game_manager.add_game(window_manager, make_current=True)
