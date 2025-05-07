import pygame as pg
import sys
from typing import Any
from types import SimpleNamespace
from .dev_console import DeveloperConsole, Logger, OutputRedirector
from .dev_overlay_element import DeveloperOverlayElement
from .input_box import Autocomplete
from .assets import load_file_stream
from .mousemotion2 import MOUSEMOTION_2


class DeveloperOverlay(DeveloperOverlayElement):
    PRIMARY_COLOR: tuple[int, int, int] = (76, 88, 68)
    SECONDARY_COLOR: tuple[int, int, int] = (62, 70, 55)
    PRIMARY_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
    SECONDARY_TEXT_COLOR: tuple[int, int, int] = (216, 222, 211)
    BORDER_COLOR_DARK: tuple[int, int, int] = (40, 46, 34)
    BORDER_COLOR_LIGHT: tuple[int, int, int] = (136, 145, 128)
    HIGHLIGHT_COLOR: tuple[int, int, int] = (150, 135, 50)
    ERROR_COLOR: tuple[int, int, int] = (255, 64, 64)

    def __init__(self,
                 namespaces: dict[str:Any],
                 surface: pg.Surface,
                 *,
                 enable_cheats: bool = False,
                 primary_font_override: pg.font.Font | None = None,
                 secondary_font_override: pg.font.Font | None = None,
                 logger_font_override: pg.font.Font | None = None):
        super().__init__(self, None, pg.Rect((0, 0), surface.get_size()))
        self.surface = surface
        self.font = primary_font_override or pg.font.Font(load_file_stream("clacon2.ttf"), 20)
        self.font2 = secondary_font_override or pg.font.Font(load_file_stream("trebuc.ttf"), 12)

        self.cheats_enabled: bool = enable_cheats

        self._logger = Logger(self.surface, font_override=logger_font_override)
        self.open: bool = False

        self.char_width = self.font.render("A", False, (255, 255, 255)).get_width()
        self.char_height = self.font.get_height()
        self.border_offset = 4

        self.autocomplete = Autocomplete(self, (0, 0))
        self.dev_console = DeveloperConsole(self)
        self.children.append(self.dev_console)

        self._developer_mode = False

        self.namespace = SimpleNamespace(dev_console=self.dev_console, pg=pg, **namespaces)
        sys.stdout = OutputRedirector(self.dev_console.log.print, self._logger.print)

    def handle_events(self, events: list[pg.event.Event]):
        # TODO: LOTS of shared code with DevOverlayElement.handle_event_recursively. Merge?
        for event in events:
            # First, we check if the autocomplete is open. If it is, it has absolute priority.
            if self.autocomplete.show:
                if self.autocomplete.handle_event(event):
                    continue

            if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                if not self.get_selected_element():
                    self.selected_child = self.children[0]
                    continue
                self.get_selected_element().select_next()
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

    def render(self):
        if not self.open:
            for child in self.children:
                if getattr(child, "pinned", False):
                    child.render_recursively(self.surface)
            if self._developer_mode:  # todo: duplicate code
                self._logger.render(self.surface)
            return

        self.surface.fill(self.PRIMARY_COLOR, special_flags=pg.BLEND_RGB_MULT)

        if self._developer_mode:
            self._logger.render(self.surface)

        for child in self.children:
            child.render_recursively(self.surface)

        if self.autocomplete.show:
            self.autocomplete.draw()
            self.surface.blit(self.autocomplete.surface, (self.autocomplete.rect.left + self.autocomplete.input_box.get_letter_x(self.autocomplete.position),
                                                     self.autocomplete.rect.top))

        if self.get_selected_element():
            pg.draw.rect(self.surface, (255, 255, 255), self.get_selected_element().get_absolute_rect(), 2)
