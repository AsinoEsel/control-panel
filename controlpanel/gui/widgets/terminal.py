from .widget import Widget, Desktop
from .log import Log
from .input_box import InputBox
from controlpanel.gui.window_manager.window_manager_setup import DEFAULT_FONT, DEFAULT_GAP, CHAR_HEIGHT


class Terminal(Widget):
    def __init__(self, name: str, parent: 'Desktop', x: int, y: int, w: int, h: int, font=DEFAULT_FONT) -> None:
        super().__init__(name, parent, x, y, w, h)
        self.add_element(Log(name + "Log", self, DEFAULT_GAP, DEFAULT_GAP, w-2*DEFAULT_GAP, h-CHAR_HEIGHT[font]*1.3-3*DEFAULT_GAP, font))
        self.add_element(InputBox(name + "InputBox", self, DEFAULT_GAP, h-DEFAULT_GAP-CHAR_HEIGHT[font]*1.3, w-2*DEFAULT_GAP, CHAR_HEIGHT[font]*1.3))
        self.active_element = self.elements[1]
