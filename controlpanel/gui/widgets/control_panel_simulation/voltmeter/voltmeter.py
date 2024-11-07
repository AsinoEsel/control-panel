from builtins import int
import pygame as pg

from ....widgets import Widget
from controlpanel.micropython_sdk.devices.dummy.voltmeter import DummyVoltmeter
from artnet import ArtNet


class VirtualVoltmeter(Widget, DummyVoltmeter):
    SIZE = 30
    NEEDLE_LENGTH = SIZE//2
    BACKGROUND_COLOR = (255, 255, 255)
    NEEDLE_COLOR = (0, 0, 0)

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, *, universe: int | None = None, intensity_function=None, noise_intensity: float = 0.02):
        super().__init__(name, parent, position[0], position[1], self.SIZE, self.SIZE, elements=None)
        DummyVoltmeter.__init__(self, artnet, name, universe=universe, intensity_function=intensity_function, noise_intensity=noise_intensity)

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        DummyVoltmeter.update(self)
        if self.intensity_function is not None or self.noise_intensity != 0.0:
            self.flag_as_needing_rerender()

    def render_body(self) -> None:
        self.surface.fill(self.BACKGROUND_COLOR)
        start_pos = pg.Vector2(self.SIZE//2, self.SIZE)
        end_pos = start_pos + pg.Vector2(0, -self.NEEDLE_LENGTH).rotate(self.intensity * 90 - 45)
        pg.draw.line(self.surface, self.NEEDLE_COLOR, start_pos, end_pos, 2)
