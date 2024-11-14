from .example_game import ExampleGame
from controlpanel.scripts import ControlAPI

ControlAPI.add_game(ExampleGame(), make_current=False)
