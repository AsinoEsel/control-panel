from .widget import Widget
import pygame as pg


class Image(Widget):
    def __init__(self, parent: Widget, x, y, w, h, image_path: str) -> None:
        super().__init__(parent, x, y, w, h, None)
        image_surface = pg.image.load(image_path)
        self.surface = pg.transform.scale(image_surface, self.surface.get_size())
    
    def render(self):
        self.render_border()
        self.blit_from_children()
