import os
import pygame as pg
from typing import TYPE_CHECKING
from .dev_windows import Window, VariableMonitorWindow
from .dev_console import DeveloperConsole
from controlpanel.game_manager.utils import MOUSEMOTION_2
if TYPE_CHECKING:
    from controlpanel.game_manager import GameManager


class DeveloperOverlay:
    def __init__(self,
                 game_manager: "GameManager",
                 render_size: tuple[int, int],
                 *,
                 font_name: str = os.path.join(os.path.dirname(__file__), "assets", "clacon2.ttf"),
                 font_size: int = 20,
                 font_name2: str = os.path.join(os.path.dirname(__file__), "assets", "trebuc.ttf"),
                 font_size2: int = 12):
        try:
            self.font: pg.font.Font = pg.font.Font(font_name, font_size)
        except FileNotFoundError:
            self.font: pg.font.Font = pg.font.Font(None, font_size)
        try:
            self.font2: pg.font.Font = pg.font.Font(font_name2, font_size2)
        except FileNotFoundError:
            self.font2: pg.font.Font = pg.font.Font(None, font_size2)
        self.game_manager = game_manager
        self.render_size: tuple[int, int] = render_size
        self.open: bool = False
        self.dark_surface = pg.Surface(render_size)
        self.dark_surface.fill((100, 100, 100))

        self.primary_color = (76, 88, 68)
        self.secondary_color = (62, 70, 55)
        self.primary_text_color = (255, 255, 255)
        self.secondary_text_color = (216, 222, 211)
        self.border_color_dark = (40, 46, 34)
        self.border_color_bright = (136, 145, 128)
        self.highlight_color = (150, 135, 50)
        self.error_color = (255, 64, 64)

        self.char_width = self.font.render("A", False, (255, 255, 255)).get_width()
        self.char_height = self.font.get_height()
        self.border_offset = 6

        self.dev_console = DeveloperConsole(self)
        self.windows: list[Window] = [
            Window(self, None, pg.Rect((100, 250, 400, 300)), title="Window"),
            VariableMonitorWindow(self, None, pg.Rect((650, 450, 400, 300)))
        ]

    def handle_events(self, events: list[pg.event.Event]):
        for event in events:
            if event.type == pg.MOUSEMOTION:
                mouse_motion2 = pg.event.Event(MOUSEMOTION_2, event.dict)
                mouse_motion2.pos = (event.pos[0] - event.rel[0], event.pos[1] - event.rel[1])
                for window in self.windows:
                    if not window.rect.collidepoint(mouse_motion2.pos):
                        continue
                    if window.handle_event_recursively(mouse_motion2):
                        break
            if self.dev_console.handle_event(event):
                return
            for window in self.windows:
                if hasattr(event, "pos") and not window.rect.collidepoint(event.pos):
                    continue
                if window.handle_event_recursively(event):
                    return

    def render(self, surface: pg.Surface):
        if not self.open:
            for window in self.windows:
                if window.pinned:
                    surface.blit(window.surface, window.rect)
            return

        surface.blit(self.dark_surface, (0, 0), special_flags=pg.BLEND_RGB_MULT)

        self.dev_console.render(surface)
        for window in self.windows:
            window.render_recursively(surface)
        if self.dev_console.autocomplete.show:
            surface.blit(self.dev_console.autocomplete.surface, (self.border_offset + self.dev_console.autocomplete.position * self.char_width, self.dev_console.surface.get_height()))

