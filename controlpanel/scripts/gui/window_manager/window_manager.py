from .window_manager_setup import *
from .event_queue import event_queue
from controlpanel.scripts.gui.widgets import Desktop
from controlpanel.game_manager import BaseGame
from controlpanel.game_manager.dev_console import console_command


class WindowManager(BaseGame):
    def __init__(self):
        super().__init__(name="Window Manager", resolution=RENDER_SIZE)
        self.desktops: dict[str: Desktop] = dict()
        self.desktop: Desktop | None = None
        self.event_queue = event_queue
        self.tick = 0

    @console_command(show_return_value=True)
    def test_cmd(self, text: str, repeats: int = 1, mystery="?") -> str:
        """
        Das ist ein Docstring.
        """
        print(text * int(repeats))
        return self.desktop.name

    @console_command(is_cheat_protected=True)
    def create_new_desktop(self, name: str, *, make_selected: bool = False) -> Desktop:
        if self.desktops.get(name) is not None:
            raise ValueError(f"Cannot create desktop: desktop with name {name} already exists!")
        new_desktop = Desktop(name)
        self.desktops[name] = new_desktop
        if make_selected:
            self.desktop = new_desktop
        return new_desktop

    @console_command(is_cheat_protected=True)
    def change_desktop(self, name_or_index: str | int):
        if isinstance(name_or_index, str):
            desktop = self.desktops.get(name_or_index)
        elif isinstance(name_or_index, int):
            if 0 <= name_or_index < len(self.desktops):
                desktop = list(self.desktops.values())[name_or_index]
            else:
                print(f"Desktop #{name_or_index+1} does not exist.")
                return
        else:
            raise ValueError("arg needs to be of type str or int")
        if desktop is not None and desktop is not self.desktop:
            from controlpanel.scripts import ControlAPI
            ControlAPI.fire_event(self.__class__.__name__, "ChangeDesktop", desktop.name)
            self.desktop = desktop

    def handle_events(self, events: list[pg.event.Event]) -> None:
        if not self.desktop:
            return
        for event in events:
            if event.type == pg.KEYDOWN and pg.key.get_mods() & pg.KMOD_CTRL and pg.K_0 <= event.key <= pg.K_9:
                self.change_desktop(event.key - pg.K_0 - 1)
                continue
            self.desktop.handle_event(event)

    def update(self) -> None:
        if not self.desktop:
            return
        self.tick += 1
        self.event_queue.update()
        self.desktop.propagate_update(self.tick, dt=self.dt, joysticks=self._joysticks)

    def render(self) -> None:
        if not self.desktop:
            return
        self.screen.blit(self.desktop.surface, (0, 0))
