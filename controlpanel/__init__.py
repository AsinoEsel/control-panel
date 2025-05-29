import contextlib
import importlib

# This gets rid of the pygame "support prompt" on import by redirecting it into the void
with contextlib.redirect_stdout(None):
    importlib.import_module("pygame")

from controlpanel.game_manager.games import BaseGame
from anaconsole import console_command, Autocomplete
