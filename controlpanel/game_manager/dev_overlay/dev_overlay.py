import os
import pygame as pg
from typing import TYPE_CHECKING, Callable, Any
from .dev_console import DeveloperConsole
from .dev_overlay_element import DeveloperOverlayElement
from .input_box import Autocomplete
from controlpanel.game_manager.utils import MOUSEMOTION_2
if TYPE_CHECKING:
    from controlpanel.game_manager import GameManager


class DeveloperOverlay:
    PRIMARY_COLOR: tuple[int, int, int] = (76, 88, 68)
    SECONDARY_COLOR: tuple[int, int, int] = (62, 70, 55)
    PRIMARY_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
    SECONDARY_TEXT_COLOR: tuple[int, int, int] = (216, 222, 211)
    BORDER_COLOR_DARK: tuple[int, int, int] = (40, 46, 34)
    BORDER_COLOR_LIGHT: tuple[int, int, int] = (136, 145, 128)
    HIGHLIGHT_COLOR: tuple[int, int, int] = (150, 135, 50)
    ERROR_COLOR: tuple[int, int, int] = (255, 64, 64)

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

        self.char_width = self.font.render("A", False, (255, 255, 255)).get_width()
        self.char_height = self.font.get_height()
        self.border_offset = 4

        self.autocomplete = Autocomplete(self, (0, 0))
        self.dev_console = DeveloperConsole(self)
        self.selected_child: DeveloperOverlayElement | None = None
        self.children: list[DeveloperOverlayElement] = [
            self.dev_console,
        ]

    def get_selected_element(self) -> DeveloperOverlayElement | None:
        current = self
        while current.selected_child is not None:
            current = current.selected_child
        return current if current is not self else None

    def handle_events(self, events: list[pg.event.Event]):
        # TODO: LOTS of shared code with DevOverlayElement.handle_event_recursively. Merge?
        for event in events:
            # First, we check if the autocomplete is open. If it is, it has absolute priority.
            if self.autocomplete.show:
                if self.autocomplete.handle_event(event):
                    continue

            # If it's a MOUSEMOTION event, we immediately fire our own MOUSEMOTION_2 event.
            # This makes it so that elements are notified when the cursor moves away from them.
            if event.type == pg.MOUSEMOTION:
                mouse_motion2 = pg.event.Event(MOUSEMOTION_2, event.dict.copy())
                mouse_motion2.pos = (event.pos[0] - event.rel[0], event.pos[1] - event.rel[1])
                for child in self.children:
                    if not child.rect.collidepoint(mouse_motion2.pos):
                        continue
                    if child.handle_event_recursively(mouse_motion2):
                        break

            # We prioritize the selected element if it exists.
            if event.type != pg.MOUSEBUTTONDOWN and self.get_selected_element():
                event_copy = pg.event.Event(event.type, event.dict)

                if hasattr(event, "pos"):
                    current = self
                    while current != self.get_selected_element():
                        current = current.selected_child
                        event_copy.pos = (event.pos[0] - current.rect.left, event.pos[1] - current.rect.top)

                if self.get_selected_element().handle_event(event_copy):
                    continue

            # We finally propagate the event normally down the tree
            for child in self.children:
                if hasattr(event, "pos") and not child.rect.collidepoint(event.pos):
                    continue
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.selected_child = child
                if child.handle_event_recursively(event):
                    return

            # Deselection in case nothing was clicked on
            if event.type == pg.MOUSEBUTTONDOWN and not any(child.rect.collidepoint(event.pos) for child in self.children):
                self.selected_child = None

    def render(self, surface: pg.Surface):
        if not self.open:
            for child in self.children:
                if getattr(child, "pinned", False):
                    child.render_recursively(surface)
            return

        surface.fill(self.PRIMARY_COLOR, special_flags=pg.BLEND_RGB_MULT)

        for child in self.children:
            child.render_recursively(surface)
        if self.autocomplete.show:
            self.autocomplete.draw()
            surface.blit(self.autocomplete.surface, (self.autocomplete.rect.left + self.autocomplete.input_box.get_letter_x(self.autocomplete.position),
                                                     self.autocomplete.rect.top))
