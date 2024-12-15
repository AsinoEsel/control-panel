from .window_manager import WindowManager
from controlpanel.scripts import ControlAPI

ControlAPI.add_game(WindowManager(), make_current=True)
