import pygame as pg
from .dev_overlay_element import DeveloperOverlayElement
from .checkbox import Checkbox
from .button import Button
from .slider import Slider
from .input_box import InputBox
from .window import Window
from .color_picker import ColorButton
from typing import Callable, TYPE_CHECKING, Optional, Any, get_type_hints, get_origin
from types import MethodType
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay


class VariableMonitor(DeveloperOverlayElement):
    class Variable(DeveloperOverlayElement):
        def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect,
                     var_name: str, var_type: type, var_getter: Callable[[], Any], var_setter: Callable[[Any], None], **kwargs):
            super().__init__(overlay, parent, rect)
            self.name: str = var_name
            self.type: type = var_type
            self.getter: Callable[[], Any] = var_getter
            self.setter: Callable[[Any], None] = var_setter

            if var_type in (int, float):
                value_range: tuple[int | float, int | float] = kwargs.get("value_range") if kwargs.get("value_range") else (0, 255) if var_type is int else (0.0, 1.0)
                self.children.append(Slider(overlay, self, pg.Rect(self.rect.centerx, 0, self.rect.w//2, self.rect.h), var_type, value_range, var_getter, var_setter))
            elif var_type == tuple[int, int, int]:
                height: int = self.rect.h - 2 * self.overlay.border_offset
                offset: int = (self.rect.h - height) // 2
                self.children.append(ColorButton(overlay, self, pg.Rect(self.rect.centerx, offset, self.rect.w//2-offset, height), var_getter, var_setter))
            # elif var_type == tuple[float, float, float]:
            #     print("FLOATTUPLE")
            elif var_type is bool:
                offset: int = (self.rect.h - Checkbox.SIZE) // 2
                self.children.append(Checkbox(overlay, self, (self.rect.right-Checkbox.SIZE-offset, offset), var_setter, var_getter))
            elif var_type is str:
                height: int = self.rect.h - 2 * self.overlay.border_offset
                offset: int = (self.rect.h - height) // 2
                self.children.append(InputBox(overlay, self, pg.Rect(self.rect.centerx, offset, self.rect.w//2-offset, height),
                                              getter=var_getter,
                                              setter_sending=var_setter))
            elif isinstance(var_setter, MethodType):
                height: int = self.rect.h - 2 * self.overlay.border_offset
                offset: int = (self.rect.h - height) // 2
                self.children.append(Button(overlay, self, pg.Rect(self.rect.centerx, offset, self.rect.w//2-offset, height),
                                            callback=var_setter,
                                            image=overlay.font2.render(f"Run {var_setter.__name__}", False, overlay.PRIMARY_TEXT_COLOR, overlay.PRIMARY_COLOR)))

            else:
                print(f"No match for {var_type}")

        def render(self):
            super().render()
            name_surf = self.overlay.font2.render(self.name, False, self.overlay.PRIMARY_TEXT_COLOR, self.overlay.PRIMARY_COLOR)
            val = self.getter()
            if isinstance(val, float):
                val = round(val, 2)
            val_surf = self.overlay.font2.render(str(val), False, self.overlay.SECONDARY_TEXT_COLOR, self.overlay.PRIMARY_COLOR)
            offset = self.rect.h//2 - name_surf.get_height() // 2
            self.surface.blit(name_surf, (2 * offset, offset))
            edit_element_width = self.children[0].rect.w if self.children else 0
            self.surface.blit(val_surf, (self.rect.w - edit_element_width - val_surf.get_width() - offset, offset))

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect):
        super().__init__(overlay, parent, rect)
        self.variables: list[VariableMonitor.Variable] = []
        self.variable_height: int = int(overlay.char_height * 1.75) // 2 * 2

    def register_variable(self, obj: object, attr: str, name: str = None, **kwargs: dict[str:Any]):
        rect = pg.Rect(0, len(self.children) * self.variable_height, self.rect.w, self.variable_height)
        var_name = name or attr
        var_type = get_type_hints(obj.__class__).get(attr) or get_type_hints(obj.__class__.__init__).get(attr) or type(getattr(obj, attr))
        if callable(getattr(obj, attr)):
            variable = VariableMonitor.Variable(self.overlay, self, rect, var_name, var_type, lambda: "", getattr(obj, attr), **kwargs)
            self.children.append(variable)
        else:
            def getter(): return getattr(obj, attr)
            def setter(var): setattr(obj, attr, var)
            variable = VariableMonitor.Variable(self.overlay, self, rect, var_name, var_type, getter, setter, **kwargs)
            self.children.append(variable)


class VariableMonitorWindow(Window):
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect):
        super().__init__(overlay, parent, rect, title="Variable Monitor Window")
        self.children.append(VariableMonitor(overlay, self, self.body_rect))
