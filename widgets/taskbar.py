from .widget import Widget
from window_manager_setup import RENDER_WIDTH


class Taskbar(Widget):
    def __init__(self, parent: Widget|None, height: int) -> None:
        x = parent.position.x if parent else 0
        y = parent.position.y if parent else 0
        w = parent.surface.get_width() if parent else RENDER_WIDTH
        super().__init__(parent, x, y, w, height)
