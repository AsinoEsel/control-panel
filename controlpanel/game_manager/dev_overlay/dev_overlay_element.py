import pygame as pg
from typing import TYPE_CHECKING, Optional, Union
from controlpanel.game_manager.utils import draw_border_rect
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay
    from .window import Window


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

    def get_absolute_rect(self) -> pg.Rect:
        from .dev_overlay import DeveloperOverlay
        current = self
        current_x, current_y = 0, 0
        while not isinstance(current, DeveloperOverlay):
            current_x += current.rect.left
            current_y += current.rect.top
            current = current.parent
        return pg.Rect(current_x, current_y, self.rect.w, self.rect.h)

    def get_parent_window(self) -> Union["Window", None]:
        from .window import Window
        from .dev_overlay import DeveloperOverlay
        current = self
        while not isinstance(current, Window):
            if isinstance(current, DeveloperOverlay):
                return None
            current = current.parent
        return current

    def is_selected(self) -> bool:
        if self.selected_child is not None:  # not the last selected object in the linked list
            return False
        current = self
        while current is not self.overlay:  # recursively walk up the parent hierarchy
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
        self.surface.fill(self.overlay.PRIMARY_COLOR)
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0,
                         self.overlay.BORDER_COLOR_LIGHT, self.overlay.BORDER_COLOR_DARK)

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
