from ....widgets import Widget
from controlpanel.event_manager.dummy.pwm import DummyPWM
import pygame as pg
from artnet import ArtNet


class VirtualPWM(Widget, DummyPWM):
    SIZE = 16

    def __init__(self, artnet: ArtNet, parent, position: tuple[int, int], name: str) -> None:
        super().__init__(name, parent, position[0], position[1], self.SIZE, self.SIZE, None)
        DummyPWM.__init__(self, artnet, name)

    def get_color(self) -> tuple[int, int, int]:
        brightness = int(self.intensity * 255)
        return brightness, brightness, brightness

    def parse_dmx_data(self, data: bytes):
        super().parse_dmx_data(data)
        self.flag_as_needing_rerender()

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]) -> None:
        DummyPWM.update(self)
        if self.intensity_function is not None:
            self.flag_as_needing_rerender()

    def render_body(self) -> None:
        self.surface.fill(self.get_color())


class VirtualLED(VirtualPWM):
    def __init__(self, artnet: ArtNet, parent, position: tuple[int, int], name: str, led_color: tuple[int, int, int] = (255, 255, 255)) -> None:
        super().__init__(artnet, parent, position, name)
        self.led_color = led_color

    def get_color(self) -> tuple[int, int, int]:
        return tuple(int(self.led_color[i] * self.intensity) for i in range(3))
