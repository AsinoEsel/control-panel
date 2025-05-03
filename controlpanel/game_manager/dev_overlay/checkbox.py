import pygame as pg
import os
from controlpanel.game_manager.utils import draw_border_rect
from .dev_overlay_element import DeveloperOverlayElement
from typing import Callable, TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class Checkbox(DeveloperOverlayElement):
    SIZE = 18
    CHECK_IMAGE: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "check.png"))

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"],
                 position: tuple[int, int],
                 callback: Callable[[bool], None],
                 getter: Callable[[], bool] | None = None
                 ):
        super().__init__(overlay, parent, pg.Rect(position, (self.SIZE, self.SIZE)))
        self.getter: Callable[[], bool] = getter
        self.setter: Callable[[bool], None] = callback

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONDOWN:
            self.setter(not self.getter())
            return True
        return False

    def render(self):
        self.surface.fill(self.overlay.SECONDARY_COLOR)
        if self.getter():
            self.surface.blit(self.CHECK_IMAGE, (0, 0))
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0, self.overlay.BORDER_COLOR_DARK, self.overlay.BORDER_COLOR_LIGHT)
