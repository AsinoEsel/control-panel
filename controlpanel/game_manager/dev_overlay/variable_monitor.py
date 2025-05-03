import pygame as pg
from .dev_overlay_element import DeveloperOverlayElement
from .checkbox import Checkbox
from .slider import Slider
from .input_box import InputBox
from .window import Window
from typing import Callable, TYPE_CHECKING, Optional, Any, get_type_hints
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


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


class VariableMonitorWindow(Window):
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect):
        super().__init__(overlay, parent, rect, title="Variable Monitor Window")
        self.children.append(VariableMonitor(overlay, self, self.body_rect))
