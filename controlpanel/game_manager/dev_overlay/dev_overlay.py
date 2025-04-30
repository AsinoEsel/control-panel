import os
import pygame as pg
from typing import TYPE_CHECKING
from .dev_windows import Window, VariableMonitorWindow
from .dev_console import DeveloperConsole
from .dev_overlay_element import DeveloperOverlayElement
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
        self.selected_child: DeveloperOverlayElement | None = None
        self.children: list[DeveloperOverlayElement] = [
            self.dev_console,
            Window(self, self, pg.Rect((100, 250, 400, 300)), title="Window"),
            VariableMonitorWindow(self, self, pg.Rect((650, 450, 400, 300))),
        ]

    def handle_events(self, events: list[pg.event.Event]):
        # TODO: LOTS of shared code with DevOverlayElement.handle_event_recursively. Merge?
        for event in events:
            if event.type == pg.MOUSEMOTION:
                mouse_motion2 = pg.event.Event(MOUSEMOTION_2, event.dict)
                mouse_motion2.pos = (event.pos[0] - event.rel[0], event.pos[1] - event.rel[1])
                for child in self.children:
                    if not child.rect.collidepoint(mouse_motion2.pos):
                        continue
                    if child.handle_event_recursively(mouse_motion2):
                        break
            for child in self.children:
                if hasattr(event, "pos") and not child.rect.collidepoint(event.pos):
                    continue
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.selected_child = child
                if child.handle_event_recursively(event):
                    return

            if event.type == pg.MOUSEBUTTONDOWN and not any(child.rect.collidepoint(event.pos) for child in self.children):
                self.selected_child = None

    def render(self, surface: pg.Surface):
        if not self.open:
            for child in self.children:
                if child.pinned:
                    child.render_recursively(surface)
            return

        surface.blit(self.dark_surface, (0, 0), special_flags=pg.BLEND_RGB_MULT)

        for child in self.children:
            child.render_recursively(surface)
        if self.dev_console.autocomplete.show:
            surface.blit(self.dev_console.autocomplete.surface, (self.border_offset + self.dev_console.autocomplete.position * self.char_width, self.dev_console.surface.get_height()))

