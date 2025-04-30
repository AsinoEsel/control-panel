import pygame as pg
from typing import TYPE_CHECKING, Optional
from abc import abstractmethod
from controlpanel.game_manager.utils import draw_border_rect
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class DeveloperOverlayElement:
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect, *, colorkey: tuple[int, int, int] | None = None):
        self.overlay: "DeveloperOverlay" = overlay
        self.parent: DeveloperOverlayElement | None = parent
        self.rect: pg.Rect = rect
        self.surface: pg.Surface = pg.Surface(rect.size)
        if colorkey:
            self.surface.set_colorkey(colorkey)
        self.children: list[DeveloperOverlayElement] = []
        self.selected_child: DeveloperOverlayElement | None = None

    def is_selected(self) -> bool:
        if self.selected_child is not None:  # not the last selected object in the linked list
            return False
        current = self
        while current.parent is not None:  # recursively walk up the parent hierarchy to check if the linked list
            if current.parent.selected_child is not current:  # if link is broken, not selected
                return False
            else:
                current = current.parent
        return True  # we reached the top of the linked list, so we are the selected object

    def render_recursively(self, surface: pg.Surface):
        self.render()
        for child in self.children:
            child.render_recursively(self.surface)
        surface.blit(self.surface, self.rect)

    def render_body(self):
        self.surface.fill(self.overlay.primary_color)
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0,
                         self.overlay.border_color_bright, self.overlay.border_color_dark)

    def render(self):
        self.render_body()

    def handle_event_recursively(self, event: pg.event.Event):
        if hasattr(event, "pos"):
            event.pos = (event.pos[0] - self.rect.left, event.pos[1] - self.rect.top)

        if self.handle_event(event):
            return True  # eaten by itself

        for child in self.children:
            if hasattr(event, "pos") and not child.rect.collidepoint(event.pos):
                continue
            if event.type == pg.MOUSEBUTTONDOWN:  # TODO: child selection
                self.selected_child = child
            if child.handle_event_recursively(event):
                return True  # eaten by child

        if event.type == pg.MOUSEBUTTONDOWN and not any(child.rect.collidepoint(event.pos) for child in self.children):
            self.selected_child = None

        if hasattr(event, "pos"):
            event.pos = (event.pos[0] + self.rect.left, event.pos[1] + self.rect.top)
        return False

    def handle_event(self, event: pg.event.Event) -> bool:
        return False
