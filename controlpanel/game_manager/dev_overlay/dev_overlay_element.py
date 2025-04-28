import pygame as pg
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class DeveloperOverlayElement:
    def __init__(self, overlay: "DeveloperOverlay", rect: pg.Rect):
        self.overlay: "DeveloperOverlay" = overlay
        self.rect: pg.Rect = rect
        self.surface: pg.Surface = pg.Surface(rect.size)
