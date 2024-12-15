from ....widgets import Widget
from controlpanel.event_manager.dummy.seven_segment import DummySevenSegmentDisplay
import pygame as pg
from artnet import ArtNet


class VirtualSevenSegmentDisplay(Widget, DummySevenSegmentDisplay):
    WIDTH = 200
    HEIGHT = 50
    FONT_SIZE = 32
    TEXT_COLOR = (255, 0, 0)
    BACKGROUND_COLOR = (0, 0, 0)

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, digits: int):
        super().__init__(name, parent, position[0], position[1], self.WIDTH, self.HEIGHT, None)
        DummySevenSegmentDisplay.__init__(self, artnet, name, digits)
        self.font = pg.font.Font("controlpanel/scripts/gui/media/DSEG7Classic-Italic.ttf", 32)

    def parse_dmx_data(self, data: bytes):
        super().parse_dmx_data(data)
        self.flag_as_needing_rerender()

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        DummySevenSegmentDisplay.update(self)

    def render_body(self):
        self.surface.fill(self.BACKGROUND_COLOR)
        self.surface.blit(self.font.render(self.text, True, self.TEXT_COLOR, self.BACKGROUND_COLOR), (0, 0))
