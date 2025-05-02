import pygame as pg
from controlpanel.game_manager.utils import draw_border_rect, maprange, MOUSEMOTION_2
from .dev_overlay_element import DeveloperOverlayElement
from .color_picker import ColorPicker
from .slider import Slider
from typing import TYPE_CHECKING, Callable, Any, get_type_hints, Optional, Type, Union
import os
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class Button(DeveloperOverlayElement):
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect, callback: Callable[[], None], *, image: pg.Surface | None = None, toggle: bool = False):
        super().__init__(overlay, parent, rect)
        self.callback: Callable[[], None] = callback
        self.image: pg.Surface | None = image
        self.toggle: bool = toggle
        if toggle:
            self.state: bool = False
        self.highlighted: bool = False
        self.pressed: bool = False

    def render(self):
        self.surface.fill(self.overlay.PRIMARY_COLOR)
        if self.image:
            tinted_image = self.image.copy()
            if self.toggle and self.state:
                tinted_image.fill(self.overlay.HIGHLIGHT_COLOR, special_flags=pg.BLEND_RGB_MULT)
            if self.pressed:
                tinted_image.fill(self.overlay.SECONDARY_TEXT_COLOR, special_flags=pg.BLEND_RGB_MULT)
            dest = ((self.rect.w - self.image.get_width()) // 2, (self.rect.h - self.image.get_height()) // 2)
            self.surface.blit(tinted_image, dest if not self.pressed else (dest[0]+1, dest[1]+1))

        if self.pressed:
            draw_border_rect(self.surface,
                             (0, 0, self.rect.w, self.rect.h), 0,
                             self.overlay.BORDER_COLOR_DARK, self.overlay.BORDER_COLOR_LIGHT)
        else:
            draw_border_rect(self.surface,
                             (0, 0, self.rect.w, self.rect.h), 0,
                             self.overlay.BORDER_COLOR_LIGHT, self.overlay.BORDER_COLOR_DARK)

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEMOTION:
            if self.is_selected() and pg.mouse.get_pressed()[0]:
                self.pressed = True
            self.highlighted = True
            return True
        elif event.type == MOUSEMOTION_2:
            if not 0 < event.pos[0] + event.rel[0] < self.rect.w or not 0 < event.pos[1] + event.rel[1] < self.rect.h:
                self.pressed = False
                self.highlighted = False
                self.render()
                return True
        elif event.type == pg.MOUSEBUTTONDOWN:
            self.pressed = True
        elif event.type == pg.MOUSEBUTTONUP and self.is_selected():
            self.pressed = False
            if self.toggle:
                self.state = not self.state
            self.callback()
            return True
        return False


class Checkbox(DeveloperOverlayElement):
    SIZE = 18
    CHECK_IMAGE: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "check.png"))

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"],
                 position: tuple[int, int],
                 callback: Callable[[bool], None],
                 getter: Callable[[], bool] | None = None, *,
                 start_checked: bool | None = None):
        super().__init__(overlay, parent, pg.Rect(position, (self.SIZE, self.SIZE)))
        self.getter: Callable[[], bool] = getter  # if getter else lambda: self.checked
        self.callback: Callable[[bool], None] = callback
        # self.checked: bool = getter() if getter else (start_checked if start_checked is not None else False)

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONDOWN:
            self.callback(not self.getter())
            return True
        return False

    def render(self):
        self.surface.fill(self.overlay.SECONDARY_COLOR)
        if self.getter():
            self.surface.blit(self.CHECK_IMAGE, (0, 0))
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0, self.overlay.BORDER_COLOR_DARK, self.overlay.BORDER_COLOR_LIGHT)


class Window(DeveloperOverlayElement):
    close_button_image: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "x.png"))
    pin_button_image: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "pin.png"))
    button_size: int = 14

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect, title: str):
        super().__init__(overlay, parent, rect)
        self.title: str = title
        close_button: Button = Button(overlay, self, pg.Rect(self.rect.w - self.overlay.border_offset - self.button_size,
                                                             self.overlay.border_offset,
                                                             self.button_size, self.button_size), self.close, image=self.close_button_image)
        pin_button: Button = Button(overlay, self,
                                    pg.Rect(self.rect.w - 2 * self.button_size - 2 * self.overlay.border_offset,
                                            self.overlay.border_offset,
                                            self.button_size, self.button_size), self.toggle_pinned, image=self.pin_button_image, toggle=True)
        self.children.append(close_button)
        self.children.append(pin_button)
        self.body_rect = pg.Rect(self.overlay.border_offset,
                                 self.overlay.border_offset + self.overlay.char_height,
                                 self.rect.w - 2 * self.overlay.border_offset,
                                 self.rect.h - 2 * self.overlay.border_offset - self.overlay.char_height)

    def toggle_pinned(self):
        self.pinned = not self.pinned

    def close(self):
        self.overlay.children.remove(self)
        del self

    def render(self):
        super().render()
        self.render_header()

    def render_header(self):
        title_surface = self.overlay.font.render(self.title, False, self.overlay.PRIMARY_TEXT_COLOR, self.overlay.PRIMARY_COLOR)
        self.surface.blit(title_surface, (self.overlay.border_offset, self.overlay.border_offset))

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEMOTION and pg.mouse.get_pressed()[0] and not any(child.rect.collidepoint(event.pos) for child in self.children) and self.is_selected():
            self.rect.move_ip(event.rel)
            # self.rect.right = min(self.rect.right, self.parent.rect.right)  # TODO: clamp window position
            # ...
            return True
        return False


class VariableMonitorWindow(Window):
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect):
        super().__init__(overlay, parent, rect, title="Variable Monitor Window")
        self.children.append(VariableMonitor(overlay, self, self.body_rect))


class VariableMonitor(DeveloperOverlayElement):
    class Variable(DeveloperOverlayElement):
        def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect,
                     var_name: str, var_type: type, var_getter: Callable[[], Any], var_setter: Callable[[Any], None]):
            super().__init__(overlay, parent, rect)
            self.name: str = var_name
            self.type: type = var_type
            self.getter: Callable[[], Any] = var_getter
            self.setter: Callable[[Any], None] = var_setter

            if var_type in (int, float):
                self.children.append(Slider(overlay, self, pg.Rect(self.rect.centerx, 0, self.rect.w//2, self.rect.h), var_type, (0, 255), var_getter, var_setter))
            elif var_type == tuple[int, int, int]:
                print("INTTUPLE")
            elif var_type == tuple[float, float, float]:
                print("FLOATTUPLE")
            elif var_type is bool:
                offset: int = (self.rect.h - Checkbox.SIZE) // 2
                self.children.append(Checkbox(overlay, self, (self.rect.right-Checkbox.SIZE-offset, offset), var_setter, var_getter))
            elif var_type is str:
                height: int = self.rect.h - self.overlay.border_offset
                offset: int = (self.rect.h - height) // 2
                self.children.append(InputBox(overlay, self, pg.Rect(self.rect.centerx, offset, self.rect.w//2-offset, height), setter_editing=var_setter))
            else:
                print(var_type)

        def render(self):
            super().render()
            name_surf = self.overlay.font2.render(self.name, False, self.overlay.PRIMARY_TEXT_COLOR, self.overlay.PRIMARY_COLOR)
            val_surf = self.overlay.font2.render(str(self.getter()), False, self.overlay.SECONDARY_TEXT_COLOR, self.overlay.PRIMARY_COLOR)
            offset = self.rect.h//2 - name_surf.get_height() // 2
            self.surface.blit(name_surf, (2 * offset, offset))
            edit_element_width = self.children[0].rect.w if self.children else 0
            self.surface.blit(val_surf, (self.rect.w - edit_element_width - val_surf.get_width() - offset, offset))

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect):
        super().__init__(overlay, parent, rect)
        self.variables: list[VariableMonitor.Variable] = []
        self.variable_height: int = int(overlay.char_height * 1.5) // 2 * 2

    def register_variable(self, obj: object, attr: str, name: str = None):
        rect = pg.Rect(0, len(self.children) * self.variable_height, self.rect.w, self.variable_height)
        var_name = name or attr
        var_type = get_type_hints(obj.__class__).get(attr) or get_type_hints(obj.__class__.__init__).get(attr) or type(getattr(obj, attr))
        def getter(): return getattr(obj, attr)
        def setter(var): setattr(obj, attr, var)
        variable = VariableMonitor.Variable(self.overlay, self, rect, var_name, var_type, getter, setter)
        self.children.append(variable)


class ColorPickerWindow(Window):
    SIZE: tuple[int, int] = (400, 250)
    CONFIRM_BUTTON_SIZE: tuple[int, int] = (60, 20)

    def __init__(self, overlay: "DeveloperOverlay", parent: "DeveloperOverlayElement", position: tuple[int, int]):
        super().__init__(overlay, parent, pg.Rect(position, self.SIZE), "Color Picker")
        self.children.append(ColorPicker(overlay, self, self.body_rect, lambda: self.overlay.PRIMARY_COLOR, lambda c: setattr(overlay, "PRIMARY_COLOR", c)))
        self.children.append(Button(overlay, self, pg.Rect(self.rect.w - self.CONFIRM_BUTTON_SIZE[0] - overlay.border_offset,
                                                           self.rect.h - self.CONFIRM_BUTTON_SIZE[1] - overlay.border_offset,
                                                           self.CONFIRM_BUTTON_SIZE[0],
                                                           self.CONFIRM_BUTTON_SIZE[1]), self.close,
                                    image=overlay.font2.render("Confirm", False, overlay.PRIMARY_TEXT_COLOR, overlay.PRIMARY_COLOR)))


class InputBox(DeveloperOverlayElement):
    def __init__(self, overlay: "DeveloperOverlay", parent: "DeveloperOverlayElement", rect: pg.Rect,
                 setter_editing: Callable[[str], None] = lambda x: None,
                 setter_sending: Callable[[str], None] = lambda x: None) -> None:
        super().__init__(overlay, parent, rect)
        self.setter_editing: Callable[[str], None] = setter_editing
        self.setter_sending: Callable[[str], None] = setter_sending
        self.text = ''
        self.clipboard = ''
        self.max_chars = self.surface.get_width()//self.overlay.char_width - 1
        self.caret_position = 0
        self.draw_caret = True
        self.selection_range = None
        self.history: list[str] = []
        self.history_index = 0
        self.color = (255, 255, 255)

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
                    self.clipboard = self.text[min(self.selection_range):max(self.selection_range)]
            elif event.key == pg.K_x and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    self.clipboard = self.text[min(self.selection_range):max(self.selection_range)]
                    self.erase_selection_range()
            elif event.key == pg.K_v and event.mod & pg.KMOD_CTRL:
                if clipboard := self.clipboard:
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
                space_index = max(self.text.find(' ', self.caret_position),
                                  self.text.find('.', self.caret_position))
                if space_index == -1:
                    space_index = len(self.text)
            elif amount < 0:
                space_index = max(self.text.rfind(' ', 0, max(0, self.caret_position - 1)),
                                  self.text.rfind('.', 0, max(0, self.caret_position - 1)))
            else:
                return
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
        text_surface = self.overlay.font.render(self.text, True, self.color, None)
        self.surface.blit(text_surface, (self.overlay.char_width // 3, 5))

    def render_caret(self):
        x = self.overlay.char_width * (self.caret_position + 1 / 3)
        pg.draw.line(self.surface, self.color, (x, self.overlay.char_height // 6),
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
