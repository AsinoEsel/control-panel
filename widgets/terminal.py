from .widget import Widget, Desktop
from .log import Log
from .input_box import InputBox
from window_manager_setup import DEFAULT_FONT, DEFAULT_GAP, CHAR_HEIGHT
from console_commands import handle_user_input


class Terminal(Widget):
    def __init__(self, parent: 'Desktop', x: int, y: int, w: int, h: int, font=DEFAULT_FONT) -> None:
        self.log = Log(self, DEFAULT_GAP, DEFAULT_GAP, w-2*DEFAULT_GAP, h-CHAR_HEIGHT[font]*1.3-3*DEFAULT_GAP, font)
        self.input_box = InputBox(self, DEFAULT_GAP, h-DEFAULT_GAP-CHAR_HEIGHT[font]*1.3, w-2*DEFAULT_GAP, CHAR_HEIGHT[font]*1.3)
        super().__init__(parent, x, y, w, h, elements=[self.log, self.input_box])
        self.active_element = self.elements[1]
    
    def handle_text(self, text):
        self.log.print_to_log('> ' + text)
        handle_user_input(self, text)
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.render_border()
        self.blit_from_children()
