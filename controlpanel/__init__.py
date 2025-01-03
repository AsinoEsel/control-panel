import contextlib
import importlib
# This gets rid of the pygame "support prompt" on import by redirecting it into the void
with contextlib.redirect_stdout(None):
    importlib.import_module("pygame")
from controlpanel.event_manager.commons import CONTROL_PANEL_EVENT
