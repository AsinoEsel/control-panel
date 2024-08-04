from .widget import Widget
from window_manager_setup import DEFAULT_FONT, CHAR_WIDTH, BACKGROUND_COLOR, COLOR_ACTIVE, LINE_THICKNESS_THICK
import pygame as pg
import utils


class Log(Widget):
    def __init__(self, parent: Widget, x: int, y: int, w: int, h: int, font=DEFAULT_FONT):
        super().__init__(parent, x, y, w, h)
        self.font = font
        self.max_chars = w // CHAR_WIDTH[font]
        self.surface.fill(BACKGROUND_COLOR)
    
    def print_to_log(self, text, color = COLOR_ACTIVE):
        if len(text) > self.max_chars:
            first_half, second_half = utils.break_up_string(text, self.max_chars)
            self.print_to_log(first_half, color)
            self.print_to_log('  ' + second_half.lstrip(), color)
            return
        
        font_render_surface = self.font.render(text, True, color, BACKGROUND_COLOR)
        
        dy = font_render_surface.get_height()
        # for removing (overwriting) the green line, ugly solution:
        pg.draw.line(self.surface, BACKGROUND_COLOR, (0, self.surface.get_height()),
                     (self.surface.get_width(), self.surface.get_height()), 2*LINE_THICKNESS_THICK)
        self.surface.scroll(0, -dy)
        override_rect = pg.Rect(0, self.surface.get_height()-dy, self.surface.get_width(), dy)
        pg.draw.rect(self.surface, BACKGROUND_COLOR, override_rect)
        
        self.surface.blit(font_render_surface, (CHAR_WIDTH[self.font]//3, self.surface.get_height() - dy))
        self.flag_as_needing_rerender()
    
    def render(self):
        self.render_border()
        self.blit_from_children()
