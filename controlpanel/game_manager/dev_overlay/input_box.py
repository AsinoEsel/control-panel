import pygame as pg
import pyperclip
from controlpanel.game_manager.utils import draw_border_rect
from .dev_overlay_element import DeveloperOverlayElement
from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class InputBox(DeveloperOverlayElement):
    STOP_CHARS: tuple[str] = (' ', '.', ',')

    def __init__(self, overlay: "DeveloperOverlay", parent: "DeveloperOverlayElement", rect: pg.Rect,
                 setter_editing: Callable[[str], None] = lambda x: None,
                 setter_sending: Callable[[str], None] = lambda x: None) -> None:
        super().__init__(overlay, parent, rect)
        self.setter_editing: Callable[[str], None] = setter_editing
        self.setter_sending: Callable[[str], None] = setter_sending
        self.text = ''
        self.max_chars = self.surface.get_width()//self.overlay.char_width - 1
        self.caret_position = 0
        self.draw_caret = True
        self.selection_range = None
        self.history: list[str] = []
        self.history_index = 0

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.TEXTINPUT and len(self.text) < self.max_chars:
            if self.selection_range:
                self.erase_selection_range()
            self.text = self.text[0:self.caret_position] + event.text + self.text[self.caret_position:]
            self.caret_position += 1
            self.setter_editing(self.text)
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.enter()
            elif event.key == pg.K_BACKSPACE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(-1, holding_ctrl=event.mod & pg.KMOD_CTRL, delete=True)
                self.setter_editing(self.text)
            elif event.key == pg.K_DELETE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(1, holding_ctrl=event.mod & pg.KMOD_CTRL, delete=True)
                self.setter_editing(self.text)
            elif event.key == pg.K_LEFT:
                self.move_caret(-1, event.mod & pg.KMOD_SHIFT, event.mod & pg.KMOD_CTRL)
            elif event.key == pg.K_RIGHT:
                self.move_caret(1, event.mod & pg.KMOD_SHIFT, event.mod & pg.KMOD_CTRL)
            elif event.key == pg.K_UP:
                if self.history_index > -len(self.history):
                    self.history_index -= 1
                    self.text = self.history[self.history_index]
                self.caret_position = len(self.text)
            elif event.key == pg.K_DOWN:
                if self.history_index < -1:
                    self.history_index += 1
                    self.text = self.history[self.history_index]
                self.caret_position = len(self.text)
            elif event.key == pg.K_a and event.mod & pg.KMOD_CTRL:
                self.selection_range = [0, len(self.text)]
            elif event.key == pg.K_c and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    pyperclip.copy(self.text[min(self.selection_range):max(self.selection_range)])
            elif event.key == pg.K_x and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    pyperclip.copy(self.text[min(self.selection_range):max(self.selection_range)])
                    self.erase_selection_range()
            elif event.key == pg.K_v and event.mod & pg.KMOD_CTRL:
                if clipboard := pyperclip.paste():
                    if self.selection_range:
                        self.erase_selection_range()
                    self.text = self.text[:self.caret_position] + clipboard + self.text[self.caret_position:]
                    self.move_caret(len(clipboard))
            else:
                return False
        else:
            return False
        return True

    def enter(self):
        if self.text:
            self.setter_sending(self.text)
            if self.text in self.history:
                self.history.remove(self.text)
            self.history.append(self.text)
        self.text = ''
        self.caret_position = 0
        self.selection_range = None
        self.history_index = 0

    def move_caret(self, amount: int, holding_shift: bool = False, holding_ctrl: bool = False, delete=False):
        original_position = self.caret_position
        if holding_ctrl:
            if amount > 0:
                indices = []
                for char in self.STOP_CHARS:
                    indices.append(self.text.find(char, self.caret_position))
                index = max(indices) if max(indices) != -1 else len(self.text)
            elif amount < 0:
                indices = []
                for char in self.STOP_CHARS:
                    indices.append(self.text.rfind(char, 0, max(0, self.caret_position - 1)))
                index = max(indices)
            else:
                return
            amount = index - self.caret_position + 1

        if not holding_shift and self.selection_range:
            if amount > 0:
                self.caret_position = max(self.selection_range)
            elif amount < 0:
                self.caret_position = min(self.selection_range)
        else:
            self.caret_position += amount
            self.caret_position = min(max(0, self.caret_position), len(self.text))

        if delete:
            self.text = self.text[:min(self.caret_position, original_position)] + self.text[max(self.caret_position,
                                                                                                original_position):]
            self.caret_position = min(self.caret_position, original_position)
        if not holding_shift:
            self.selection_range = None
        elif self.selection_range:
            self.selection_range[1] = self.caret_position
        else:
            self.selection_range = [original_position, self.caret_position]

    def erase_selection_range(self):
        self.text = self.text[0:min(self.selection_range)] + self.text[max(self.selection_range):]
        self.caret_position = min(self.selection_range)
        self.selection_range = None

    def render_text(self):
        text_surface = self.overlay.font.render(self.text, True, self.overlay.PRIMARY_TEXT_COLOR, None)
        self.surface.blit(text_surface, (self.overlay.char_width // 3, 5))

    def render_caret(self):
        x = self.overlay.char_width * (self.caret_position + 1 / 3)
        pg.draw.line(self.surface, self.overlay.PRIMARY_TEXT_COLOR, (x, self.overlay.char_height // 6),
                     (x, self.rect.height - self.overlay.char_height // 6), 2)

    def render_selection(self):
        x = int(self.overlay.char_width * (min(self.selection_range) + 1 / 3))
        y = self.overlay.char_height // 8
        w = self.overlay.char_width * (max(self.selection_range) - min(self.selection_range))
        h = self.rect.height - 2 * self.overlay.char_height // 8
        pg.draw.rect(self.surface, self.overlay.HIGHLIGHT_COLOR, (x, y, w, h))

    def render_body(self):
        self.surface.fill(self.overlay.SECONDARY_COLOR)
        if self.selection_range:
            self.render_selection()
        self.render_text()
        if self.draw_caret and not self.selection_range:
            self.render_caret()
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0, self.overlay.BORDER_COLOR_DARK, self.overlay.BORDER_COLOR_LIGHT)
