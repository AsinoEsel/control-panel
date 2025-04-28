import pygame as pg
from controlpanel.game_manager.utils import draw_border_rect
from .dev_overlay_element import DeveloperOverlayElement
from typing import TYPE_CHECKING
import os
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class Window(DeveloperOverlayElement):
    close_button_surface: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "x.png"))
    pin_button_surface: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "pin.png"))
    button_size: int = 12

    class Button:
        size: int = 12

        def __init__(self, image: pg.Surface, x: int, y: int):
            self.image: pg.Surface = image
            self.rect: pg.Rect = pg.Rect((x, y, self.size, self.size))

    def __init__(self, overlay: "DeveloperOverlay", title: str, rect: pg.Rect):
        super().__init__(overlay, rect)
        self.title: str = title
        self.pinned: bool = False
        self.close_button: Window.Button = Window.Button(self.close_button_surface,
                                                         self.rect.w - self.overlay.border_offset - self.button_size,
                                                         self.overlay.border_offset)
        self.pin_button: Window.Button = Window.Button(self.pin_button_surface,
                                                       self.rect.w - 2 * self.button_size - 2 * self.overlay.border_offset,
                                                       self.overlay.border_offset)
        self.surface = pg.Surface(rect.size)

        self.render()

    def close(self):
        self.overlay.windows.remove(self)

    def render(self):
        self.surface.fill(self.overlay.primary_color)
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0,
                                          self.overlay.border_color_bright, self.overlay.border_color_dark)
        self.render_header()
        draw_border_rect(self.surface, (self.overlay.border_offset, self.overlay.border_offset + self.overlay.char_height,
                                                         self.rect.w - 2 * self.overlay.border_offset,
                                                         self.rect.h - 2 * self.overlay.border_offset - self.overlay.char_height), 0,
                                          self.overlay.border_color_bright, self.overlay.border_color_dark)

        self.surface.blit(self.close_button_surface, self.close_button.rect)
        self.surface.blit(self.pin_button_surface, self.pin_button.rect)

    def render_header(self):
        title_surface = self.overlay.font.render(self.title, False, self.overlay.primary_text_color, self.overlay.primary_color)
        self.surface.blit(title_surface, (self.overlay.border_offset, self.overlay.border_offset))


# class VariableWindow:
#     def __init__(self, dev_console: DeveloperConsole, title: str, rect: pg.Rect, variables: list[tuple[str, type, GetterType, SetterType]] | None = None):
#         super().__init__()
#         self.variables = variables or []
