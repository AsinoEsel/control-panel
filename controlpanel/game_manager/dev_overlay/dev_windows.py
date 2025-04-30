import pygame as pg
from controlpanel.game_manager.utils import draw_border_rect, maprange, MOUSEMOTION_2
from .dev_overlay_element import DeveloperOverlayElement
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
        self.surface.fill(self.overlay.primary_color)
        if self.image:
            tinted_image = self.image.copy()
            if self.toggle and self.state:
                tinted_image.fill(self.overlay.highlight_color, special_flags=pg.BLEND_RGB_MULT)
            if self.pressed:
                tinted_image.fill(self.overlay.secondary_text_color, special_flags=pg.BLEND_RGB_MULT)
            dest = ((self.rect.w - self.image.get_width()) // 2, (self.rect.h - self.image.get_height()) // 2)
            self.surface.blit(tinted_image, dest if not self.pressed else (dest[0]+1, dest[1]+1))

        if self.pressed:
            draw_border_rect(self.surface,
                             (0, 0, self.rect.w, self.rect.h), 0,
                             self.overlay.border_color_dark, self.overlay.border_color_bright)
        else:
            draw_border_rect(self.surface,
                             (0, 0, self.rect.w, self.rect.h), 0,
                             self.overlay.border_color_bright, self.overlay.border_color_dark)

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


class Slider(DeveloperOverlayElement):
    COLOR: tuple[int, int, int] = (31, 31, 31)
    GROOVE_WIDTH: int = 6
    SLIDER_SIZE: tuple[int, int] = (12, 24)
    TRANSPARENCY: tuple[int, int, int] = (0, 0, 0)

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect,
                 domain: Type[Union[int, float]],
                 value_range: tuple[int | float, int | float],
                 getter: Callable[[], int | float],
                 setter: Callable[[int | float], None]):
        super().__init__(overlay, parent, rect, colorkey=self.TRANSPARENCY)
        self.domain = domain
        self.value_range: tuple[int | float, int | float] = value_range
        self.setter: Callable[[int | float], None] = setter
        self.getter: Callable[[], int | float] = getter
        self.groove_rect: pg.Rect = pg.Rect(self.SLIDER_SIZE[0] // 2,
                                            self.rect.h // 2 - self.GROOVE_WIDTH // 2,
                                            rect.width - 2 * self.SLIDER_SIZE[0] // 2,
                                            self.GROOVE_WIDTH)
        self.handle_rect: pg.Rect = pg.Rect(self.groove_rect.left - self.SLIDER_SIZE[0]//2,
                                            self.groove_rect.centery - self.SLIDER_SIZE[1]//2,
                                            self.SLIDER_SIZE[0],
                                            self.SLIDER_SIZE[1])

    def set_handle_position(self, value: int | float):
        self.handle_rect.left = (value - self.value_range[0]) / (
                    self.value_range[1] - self.value_range[0]) * self.groove_rect.w

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONDOWN:
            mapped_val = maprange(event.pos[0], (self.groove_rect.left, self.groove_rect.right), self.value_range)
            val = self.domain(min(self.value_range[1], max(self.value_range[0], mapped_val)))
            self.setter(val)
            return True
        return False

    def render(self):
        self.surface.fill(self.TRANSPARENCY)
        self.set_handle_position(self.getter())
        pg.draw.rect(self.surface, self.COLOR, self.groove_rect)
        draw_border_rect(self.surface, (self.groove_rect.left, self.groove_rect.top, self.groove_rect.w, self.groove_rect.h), 0, self.overlay.border_color_dark, self.overlay.border_color_bright)
        pg.draw.rect(self.surface, self.overlay.primary_color, self.handle_rect)
        draw_border_rect(self.surface, (self.handle_rect.left, self.handle_rect.top, self.handle_rect.w, self.handle_rect.h), 0, self.overlay.border_color_bright, self.overlay.border_color_dark)


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
        self.surface.fill(self.overlay.secondary_color)
        if self.getter():
            self.surface.blit(self.CHECK_IMAGE, (0, 0))
        draw_border_rect(self.surface, (0, 0, self.rect.w, self.rect.h), 0, self.overlay.border_color_dark, self.overlay.border_color_bright)


class ColorPicker(DeveloperOverlayElement):
    COLOR_PICKER_IMAGE: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "colorwheel.png"))

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], pos: tuple[int, int]):
        super().__init__(overlay, parent, pg.Rect(pos, (self.COLOR_PICKER_IMAGE.get_width()+2, self.COLOR_PICKER_IMAGE.get_height()+2)))

    def render(self):
        self.surface.fill(self.overlay.primary_color)
        self.surface.blit(self.COLOR_PICKER_IMAGE, (1, 1))
        pg.draw.circle(self.surface, self.overlay.border_color_dark, (self.rect.w//2, self.rect.h//2), self.rect.w//2, 1)
        pg.draw.circle(self.surface, self.overlay.border_color_bright, (self.rect.w//2, self.rect.h//2), self.rect.w//2, 1, draw_bottom_right=True)


class Window(DeveloperOverlayElement):
    close_button_image: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "x.png"))
    pin_button_image: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "pin.png"))
    button_size: int = 12

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect, title: str):
        super().__init__(overlay, parent, rect)
        self.title: str = title
        close_button: Button = Button(overlay, self, pg.Rect(self.rect.w - self.overlay.border_offset - self.button_size,
                                                             self.overlay.border_offset,
                                                             12, 12), self.close, image=self.close_button_image)
        pin_button: Button = Button(overlay, self,
                                    pg.Rect(self.rect.w - 2 * self.button_size - 2 * self.overlay.border_offset,
                                            self.overlay.border_offset,
                                            12, 12), self.toggle_pinned, image=self.pin_button_image, toggle=True)
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
        title_surface = self.overlay.font.render(self.title, False, self.overlay.primary_text_color, self.overlay.primary_color)
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
            else:
                print(var_type)

        def render(self):
            super().render()
            name_surf = self.overlay.font2.render(self.name, False, self.overlay.primary_text_color, self.overlay.primary_color)
            val_surf = self.overlay.font2.render(str(self.getter()), False, self.overlay.secondary_text_color, self.overlay.primary_color)
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
        variable = VariableMonitor.Variable(self.overlay, self.parent, rect, var_name, var_type, getter, setter)
        self.children.append(variable)


class ColorPickerWindow(Window):
    SIZE: tuple[int, int] = (400, 250)
    CONFIRM_BUTTON_SIZE = (60, 20)

    def __init__(self, overlay: "DeveloperOverlay", parent: "DeveloperOverlayElement", position: tuple[int, int]):
        super().__init__(overlay, parent, pg.Rect(position, self.SIZE), "Color Picker")
        self.children.append(ColorPicker(overlay, self, self.body_rect.topleft))
        self.children.append(Button(overlay, self, pg.Rect(self.rect.w - self.CONFIRM_BUTTON_SIZE[0] - overlay.border_offset,
                                                           self.rect.h - self.CONFIRM_BUTTON_SIZE[1] - overlay.border_offset,
                                                           self.CONFIRM_BUTTON_SIZE[0],
                                                           self.CONFIRM_BUTTON_SIZE[1]), self.close,
                                    image=overlay.font2.render("Confirm", False, overlay.primary_text_color, overlay.primary_color)))
