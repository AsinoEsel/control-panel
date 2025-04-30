import pygame as pg
from controlpanel.game_manager.utils import draw_border_rect, maprange
from .dev_overlay_element import DeveloperOverlayElement
from typing import TYPE_CHECKING, Callable, Any, get_type_hints, Optional, Type, Union
import os
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class Button(DeveloperOverlayElement):
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect, callback: Callable[[], None] = lambda: None, image: pg.Surface | None = None):
        super().__init__(overlay, parent, rect)
        self.image: pg.Surface | None = image
        self.pressed: bool = False
        self.push_callback: Callable[[], None] = callback

    def render(self):
        self.render_body()
        if self.image:
            self.surface.blit(self.image, (0, 0))
            if self.pressed:
                self.surface.fill(self.overlay.highlight_color, special_flags=pg.BLEND_RGB_MULT)

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONDOWN:
            self.push_callback()
            self.pressed = True
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
                 start_value: int | float | None = None,
                 callback: Callable[[int | float], None] = lambda x: None):
        super().__init__(overlay, parent, rect, colorkey=self.TRANSPARENCY)
        self.domain = domain
        self.value_range: tuple[int | float, int | float] = value_range
        self.callback: Callable[[int | float], None] = callback
        self.groove_rect: pg.Rect = pg.Rect(self.SLIDER_SIZE[0] // 2,
                                            self.rect.h // 2 - self.GROOVE_WIDTH // 2,
                                            rect.width - 2 * self.SLIDER_SIZE[0] // 2,
                                            self.GROOVE_WIDTH)
        self.value: int | float = start_value if start_value is not None else value_range[0]
        x_offset = (self.value - self.value_range[0]) / (self.value_range[1] - self.value_range[0]) * self.groove_rect.w
        self.handle_rect: pg.Rect = pg.Rect(self.groove_rect.left + x_offset - self.SLIDER_SIZE[0]//2,
                                            self.groove_rect.centery - self.SLIDER_SIZE[1]//2,
                                            self.SLIDER_SIZE[0],
                                            self.SLIDER_SIZE[1])

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONDOWN:
            mapped_val = maprange(event.pos[0], (self.groove_rect.left, self.groove_rect.right), self.value_range)
            val = self.domain(min(self.value_range[1], max(self.value_range[0], mapped_val)))
            self.handle_rect.left = (val - self.value_range[0]) / (self.value_range[1] - self.value_range[0]) * self.groove_rect.w
            self.callback(val)
            print(val)
            return True
        return False

    def render(self):
        self.surface.fill(self.TRANSPARENCY)
        pg.draw.rect(self.surface, self.COLOR, self.groove_rect)
        draw_border_rect(self.surface, (self.groove_rect.left, self.groove_rect.top, self.groove_rect.w, self.groove_rect.h), 0, self.overlay.border_color_dark, self.overlay.border_color_bright)
        pg.draw.rect(self.surface, self.overlay.primary_color, self.handle_rect)
        draw_border_rect(self.surface, (self.handle_rect.left, self.handle_rect.top, self.handle_rect.w, self.handle_rect.h), 0, self.overlay.border_color_bright, self.overlay.border_color_dark)


class Window(DeveloperOverlayElement):
    close_button_image: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "x.png"))
    pin_button_image: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "pin.png"))
    button_size: int = 12

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect, title: str):
        super().__init__(overlay, parent, rect)
        self.title: str = title
        self.pinned: bool = False
        close_button: Button = Button(overlay, self, pg.Rect(self.rect.w - self.overlay.border_offset - self.button_size,
                                                             self.overlay.border_offset,
                                                             12, 12), self.close, self.close_button_image)
        pin_button: Button = Button(overlay, self,
                                    pg.Rect(self.rect.w - 2 * self.button_size - 2 * self.overlay.border_offset,
                                            self.overlay.border_offset,
                                            12, 12), self.toggle_pinned, self.pin_button_image)
        self.children.append(close_button)
        self.children.append(pin_button)
        self.body_rect = pg.Rect(self.overlay.border_offset,
                                 self.overlay.border_offset + self.overlay.char_height,
                                 self.rect.w - 2 * self.overlay.border_offset,
                                 self.rect.h - 2 * self.overlay.border_offset - self.overlay.char_height)

    def toggle_pinned(self):
        self.pinned = not self.pinned

    def close(self):
        self.overlay.windows.remove(self)

    def render(self):
        super().render()
        self.render_header()

    def render_header(self):
        title_surface = self.overlay.font.render(self.title, False, self.overlay.primary_text_color, self.overlay.primary_color)
        self.surface.blit(title_surface, (self.overlay.border_offset, self.overlay.border_offset))

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEMOTION and pg.mouse.get_pressed()[0] and not any(child.rect.collidepoint(event.pos) for child in self.children):
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
                self.children.append(Slider(overlay, self, pg.Rect(self.rect.centerx, 0, self.rect.w//2, self.rect.h), var_type, (0, 255), 64, var_setter))
            elif var_type == tuple[int, int, int]:
                print("TUPLE")
            elif var_type == tuple[float, float, float]:
                print("FLOATTUPLE")
            else:
                print(var_type)

        def render(self):
            super().render()
            name_surf = self.overlay.font2.render(self.name, False, self.overlay.primary_text_color, self.overlay.primary_color)
            val_surf = self.overlay.font2.render(str(self.getter()), False, self.overlay.secondary_text_color, self.overlay.primary_color)
            offset = self.rect.h//2 - name_surf.get_height() // 2
            self.surface.blit(name_surf, (2 * offset, offset))
            self.surface.blit(val_surf, (self.rect.w//2 - val_surf.get_width() - offset, offset))

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect):
        super().__init__(overlay, parent, rect)
        self.variables: list[VariableMonitor.Variable] = []
        self.variable_height: int = int(overlay.char_height * 1.5)

    def register_variable(self, obj: object, attr: str, name: str = None):
        rect = pg.Rect(0, len(self.children) * self.variable_height, self.rect.w, self.variable_height)
        var_name = name or attr
        var_type = get_type_hints(obj.__class__).get(attr) or type(getattr(obj, attr))
        def getter(): return getattr(obj, attr)
        def setter(var): setattr(obj, attr, var)
        variable = VariableMonitor.Variable(self.overlay, self.parent, rect, var_name, var_type, getter, setter)
        self.children.append(variable)

    # def render(self):
    #     super().render()
    #     for variable in self.variables:
    #         font_surface = self.overlay.font.render(variable.var_name, False, self.overlay.primary_text_color, self.overlay.primary_color)
    #         self.surface.blit(font_surface, (0, 10))
