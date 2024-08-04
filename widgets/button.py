from .widget import Widget, Window
import pygame as pg
from window_manager_setup import DEFAULT_FONT


class Button(Widget):
    def __init__(self, parent: Widget|Window, x: int, y: int, w: int, h: int, text: str, callback, font: pg.font.Font=DEFAULT_FONT) -> None:
        super().__init__(parent, x, y, w, h)
        self.text = text
        self.font = font
        self.callback = callback
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            self.hit_button()
            return
        if event.type == pg.KEYUP:
            if event.key == pg.K_SPACE or event.key == pg.K_RETURN:
                self.hit_button()
                return
        super().handle_event(event)
    
    def hit_button(self):
        self.callback()
    
    def close_parent(self):
        self.parent.close()
    
    def render_text(self):
        text_surface = self.font.render(self.text, True, self.color)
        self.surface.blit(text_surface, (0, 0))
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.render_text()
        self.render_border()
        super().blit_from_children()
