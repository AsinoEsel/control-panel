import pygame as pg
import numpy as np
import os
from .dev_overlay_element import DeveloperOverlayElement
from .slider import Slider
from typing import Optional, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from .dev_overlay import DeveloperOverlay

import colorsys
import math


def generate_color_wheel(size: int) -> pg.Surface:
    radius = size // 2
    surface = pg.Surface((size, size), pg.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    for x in range(size):
        for y in range(size):
            dx = x - radius
            dy = y - radius
            distance = np.sqrt(dx ** 2 + dy ** 2) / radius
            if distance > 1:
                continue
            else:
                hue = (np.arctan2(-dy, dx) + np.pi) / (2 * np.pi)  # 0 to 1
                saturation = distance  # 0 to 1
                rgb = colorsys.hsv_to_rgb(hue, saturation, 1.0)
                rgb = tuple(int(c * 255) for c in rgb)
                surface.set_at((x, y), rgb)
    return surface


class ColorPicker(DeveloperOverlayElement):
    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], rect: pg.Rect,
                 getter: Callable[[], tuple[int, int, int]] = lambda: (0, 0, 0),
                 setter: Callable[[tuple[int, int, int]], None] = lambda color: None,
                 ):
        super().__init__(overlay, parent, rect)
        self.getter: Callable[[], tuple[int, int, int]] = getter
        self.setter: Callable[[tuple[int, int, int]], None] = setter
        self.color_wheel = ColorWheel(overlay, self, (overlay.border_offset, overlay.border_offset), getter, setter)
        self.children.append(self.color_wheel)

        sliders_x = 2 * overlay.border_offset + self.color_wheel.SIZE
        slider_width = self.rect.w - overlay.border_offset - sliders_x
        slider_dist = 30
        value_slider = Slider(overlay, self, pg.Rect(sliders_x, 10, slider_width, Slider.SLIDER_SIZE[1]), float, (0.0, 1.0),
                              self.value_getter(),
                              self.value_setter)

        sliders_y = value_slider.rect.top + slider_dist
        rgb_sliders = [Slider(overlay, self, pg.Rect(sliders_x, sliders_y + ch*slider_dist, slider_width, Slider.SLIDER_SIZE[1]), int, (0, 255), self.rgb_getter(ch), self.rgb_setter(ch)) for ch in range(3)]
        self.children.append(value_slider)
        self.children.extend(rgb_sliders)

    def value_getter(self) -> Callable[[], float]:
        return lambda: colorsys.rgb_to_hsv(*[x / 255.0 for x in self.getter()])[2]

    def value_setter(self, val: float) -> None:
        self.color_wheel.draw_color_wheel(val)
        self.color_wheel.pick_color()

    def rgb_getter(self, channel: int) -> Callable[[], int]:
        return lambda: self.getter()[channel]

    def rgb_setter(self, channel: int) -> Callable[[int], None]:
        def setter(val: int) -> None:
            color: tuple[int, int, int] = self.getter()
            rgb: tuple[int, int, int] = tuple(x if i != channel else val for i, x in enumerate(color))
            self.setter(rgb)
            self.color_wheel.draw_color_wheel()
            *self.color_wheel.caret_position, _ = self.color_wheel.rgb_to_wheel_coordinates(rgb)
        return setter


class ColorWheel(DeveloperOverlayElement):
    SIZE = 200
    WHEEL_SIZE = SIZE
    COLOR_PICKER_CARET: pg.Surface = pg.image.load(os.path.join(os.path.dirname(__file__), "assets", "color_picker_caret.png"))
    COLOR_WHEEL: pg.Surface = generate_color_wheel(SIZE)

    def __init__(self, overlay: "DeveloperOverlay", parent: Optional["DeveloperOverlayElement"], pos: tuple[int, int],
                 getter: Callable[[], tuple[int, int, int]] = lambda: (0, 0, 0),
                 setter: Callable[[tuple[int, int, int]], None] = lambda color: None,
                 ):
        super().__init__(overlay, parent, pg.Rect(pos, (self.SIZE, self.SIZE)))
        self.getter: Callable[[], tuple[int, int, int]] = getter
        self.setter: Callable[[tuple[int, int, int]], None] = setter
        caret_x, caret_y, value = self.rgb_to_wheel_coordinates(getter())
        self.caret_position: tuple[int, int] = (caret_x, caret_y)
        self.color_wheel: pg.Surface = self.COLOR_WHEEL.copy()
        self.draw_color_wheel()

    def draw_color_wheel(self, value: float | None = None):
        self.color_wheel.blit(self.COLOR_WHEEL, (0, 0))
        value: float = colorsys.rgb_to_hsv(*[x/255.0 for x in self.getter()])[2] if value is None else value
        value_norm: int = int(255 * value)
        self.color_wheel.fill((value_norm, value_norm, value_norm), special_flags=pg.BLEND_RGB_MULT)

    def rgb_to_wheel_coordinates(self, rgb: tuple[int, int, int]) -> tuple[int, int, float]:
        # Normalize RGB
        r, g, b = [c / 255.0 for c in rgb]

        # Convert RGB to HSV
        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        # Convert hue (0–1) to angle
        angle = h * 2 * math.pi

        # Convert polar (angle, s) to cartesian (x, y)
        radius = (self.WHEEL_SIZE // 2) * s
        cx = self.WHEEL_SIZE // 2
        cy = self.WHEEL_SIZE // 2
        x = int(cx - radius * math.cos(angle))
        y = int(cy + radius * math.sin(angle))  # y-axis inverted in screen coords

        return x, y, v

    def pick_color(self):
        r, g, b, a = self.color_wheel.get_at(self.caret_position)
        self.setter((r, g, b))

    def get_position_inside_wheel(self, position: tuple[int, int]) -> bool:
        return pg.Vector2(position).distance_squared_to(pg.Vector2(self.rect.w // 2, self.rect.h // 2)) < (self.SIZE // 2) ** 2

    def handle_event(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONDOWN and self.get_position_inside_wheel(event.pos):
            self.caret_position = event.pos
            self.pick_color()
            return True
        elif event.type == pg.MOUSEMOTION and pg.mouse.get_pressed()[0] and self.is_selected() and self.get_position_inside_wheel(event.pos):
            self.caret_position = event.pos
            self.pick_color()
            return True
        return False

    def render(self):
        self.surface.fill(self.overlay.PRIMARY_COLOR)
        self.surface.blit(self.color_wheel, (0, 0))
        pg.draw.circle(self.surface, self.overlay.BORDER_COLOR_DARK, (self.rect.w // 2, self.rect.h // 2), self.rect.w // 2, 1)
        pg.draw.circle(self.surface, self.overlay.BORDER_COLOR_LIGHT, (self.rect.w // 2, self.rect.h // 2), self.rect.w // 2, 1, draw_bottom_right=True)
        self.surface.blit(self.COLOR_PICKER_CARET, (self.caret_position[0] - 3, self.caret_position[1] - 3))
