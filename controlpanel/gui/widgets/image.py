from .widget import Widget
import pygame as pg


class Image(Widget):
    def __init__(self, name: str, parent: Widget, x, y, image_path: str, w=None, h=None) -> None:
        image_surface = pg.image.load(image_path)
        w = w if w is not None else image_surface.get_width()
        h = h if h is not None else image_surface.get_height()
        super().__init__(name, parent, x, y, w, h, None)
        self.surface = pg.transform.scale(image_surface, self.surface.get_size())
    
    def load_image(self, path: str, retain_size: bool = True):
        self.surface = pg.transform.scale(pg.image.load(path), self.surface.get_size()) if retain_size else pg.image.load(path)
        self.flag_as_needing_rerender()

    def render_body(self):
        pass
