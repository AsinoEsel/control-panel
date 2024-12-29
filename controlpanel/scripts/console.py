from controlpanel.scripts import ControlAPI, Event
from controlpanel.scripts.gui.widgets import Desktop, Log
from controlpanel.scripts.gui import WindowManager

@ControlAPI.callback("TerminalInputBox", "TextInput")
def console(event: Event):
    window_manager: WindowManager | None = ControlAPI.get_game("CCCGame")
    desktop: Desktop = window_manager.desktops.get("intro")
    log: Log = desktop.widget_manifest.get("TerminalLog")
    user_input = event.value

    if user_input.startswith("/help"):
        log.print_to_log("...")
    elif user_input.startswith("/"):
        split = user_input.split(" ")
        log.print_to_log(f"Unknown command: {split[0]}")
    else:
        log.print_to_log(user_input)
