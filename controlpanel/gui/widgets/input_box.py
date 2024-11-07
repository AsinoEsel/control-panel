from .widget import Widget
from controlpanel.gui.window_manager.window_manager_setup import DEFAULT_FONT, COLOR_INACTIVE, CHAR_WIDTH, CHAR_HEIGHT, LINE_THICKNESS_THIN, BACKGROUND_COLOR, TARGET_FRAME_RATE
import pygame as pg


class InputBox(Widget):
    def __init__(self, name: str, parent: Widget, x: int, y: int, w: int, h: int = None, font = DEFAULT_FONT) -> None:
        if h is None:
            h = CHAR_HEIGHT[font]*1.3
        super().__init__(name, parent, x, y, w, h)
        self.color = COLOR_INACTIVE
        self.font = font
        self.text = ''
        self.max_chars = w // CHAR_WIDTH[font]
        self.caret_position = 0
        self.draw_caret = False
        self.selection_range = None
        self.history: list[str] = []
        self.history_index = 0

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.TEXTINPUT and len(self.text) < self.max_chars:
            if self.selection_range:
                self.erase_selection_range()
            self.text = self.text[0:self.caret_position] + event.text + self.text[self.caret_position:]
            self.caret_position += 1
            self.flag_as_needing_rerender()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text:
                    # self.parent.handle_text(self.text)
                    self.fire_event("TextInput", self.text)
                    if self.text in self.history:
                        self.history.remove(self.text)
                    self.history.append(self.text)
                self.text = ''
                self.caret_position = 0
                self.selection_range = None
                self.history_index = 0
            elif event.key == pg.K_BACKSPACE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(-1, holding_ctrl=event.mod&pg.KMOD_CTRL, delete=True)
            elif event.key == pg.K_DELETE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(1, holding_ctrl=event.mod&pg.KMOD_CTRL, delete=True)
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
                    self.get_desktop().clipboard = self.text[min(self.selection_range):max(self.selection_range)]
            elif event.key == pg.K_x and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    self.get_desktop().clipboard = self.text[min(self.selection_range):max(self.selection_range)]
                    self.erase_selection_range()
            elif event.key == pg.K_v and event.mod & pg.KMOD_CTRL:
                if clipboard := self.get_desktop().clipboard:
                    if self.selection_range:
                        self.erase_selection_range()
                    self.text = self.text[:self.caret_position] + clipboard + self.text[self.caret_position:]
                    self.move_caret(len(clipboard))
            self.flag_as_needing_rerender()
        super().handle_event(event)
    
    def deactivate(self) -> None:
        self.draw_caret = False
        super().deactivate()
    
    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        if self.active:
            self.blink_caret(tick)
    
    def blink_caret(self, tick):
        blinks_per_second = 1
        ticks_per_blink = TARGET_FRAME_RATE / blinks_per_second
        if self.draw_caret == False and tick % ticks_per_blink < ticks_per_blink / 2:
            self.draw_caret = True
            self.flag_as_needing_rerender()
        elif self.draw_caret == True and tick % ticks_per_blink > ticks_per_blink / 2:
            self.draw_caret = False
            self.flag_as_needing_rerender()
    
    def move_caret(self, amount: int, holding_shift: bool = False, holding_ctrl: bool = False, delete=False):
        original_position = self.caret_position
        if holding_ctrl:
            if amount > 0:
                space_index = self.text.find(' ', self.caret_position)
                space_index = space_index if space_index != -1 else len(self.text)
            elif amount < 0:
                space_index = self.text.rfind(' ', 0, max(0, self.caret_position-1))
            amount = space_index - self.caret_position + 1
            
        if not holding_shift and self.selection_range:
            if amount > 0:
                self.caret_position = max(self.selection_range)
            elif amount < 0:
                self.caret_position = min(self.selection_range)
        else:
            self.caret_position += amount
            self.caret_position = min(max(0, self.caret_position), len(self.text))

        if delete:
            self.text = self.text[:min(self.caret_position, original_position)] + self.text[max(self.caret_position,original_position):]
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
        text_surface = self.font.render(self.text, True, self.color)
        self.surface.blit(text_surface, (CHAR_WIDTH[self.font]//3, 5))
    
    def render_caret(self):
        x = CHAR_WIDTH[self.font]*(self.caret_position+1/3)
        pg.draw.line(self.surface, self.color, (x, CHAR_HEIGHT[self.font]//6),
                                               (x, self.rect.height - CHAR_HEIGHT[self.font]//6), LINE_THICKNESS_THIN)
    
    def render_selection(self):
        x = int(CHAR_WIDTH[self.font]*(min(self.selection_range)+1/3))
        y = CHAR_HEIGHT[self.font]//8
        w = CHAR_WIDTH[self.font]*(max(self.selection_range)-min(self.selection_range))
        h = self.rect.height - 2*CHAR_HEIGHT[self.font]//8
        pixels = pg.surfarray.pixels3d(self.surface)
        pixels[x:x+w, y:y+h, 1] = 255 - pixels[x:x+w, y:y+h, 1]

    def render_body(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.render_text()
        if self.selection_range:
            self.render_selection()
        if self.draw_caret and not self.selection_range:
            self.render_caret()


class InputBoxPassword(InputBox):
    def __init__(self, parent: Widget, x: int, y: int, w: int, h: int = None, font=DEFAULT_FONT) -> None:
        super().__init__(parent, x, y, w, h, font)
        
    def render_text(self):
        hidden_text = "*" * len(self.text)
        text_surface = self.font.render(hidden_text, True, self.color)
        self.surface.blit(text_surface, (CHAR_WIDTH[self.font]//3, 5))