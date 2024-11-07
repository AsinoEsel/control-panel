from ....widgets import Widget
from controlpanel.micropython_sdk.devices.dummy.led_strip import DummyLEDStrip
import pygame as pg
from artnet import ArtNet


class VirtualLEDStrip(Widget, DummyLEDStrip):
    LED_SIZE = 16
    GRB_CHANNEL_ORDER = (1, 0, 2)

    def __init__(self, artnet: ArtNet, parent, position: tuple[int, int], name: str, length: int, *, universe: int | None = None, animation=None) -> None:
        super().__init__(name, parent, position[0], position[1], self.LED_SIZE * length, self.LED_SIZE, None)
        DummyLEDStrip.__init__(self, artnet, name, length, universe=universe, animation=animation)
        self._buffer = bytearray(3*length)
        self.led_colors = [(0, 0, 0) for _ in range(length)]
        self.led_rects = [pg.Rect(i * self.LED_SIZE, 0, self.LED_SIZE, self.LED_SIZE) for i in range(length)]

    def render_body(self):
        for rect, color in zip(self.led_rects, self.led_colors):
            pg.draw.rect(self.surface, color, rect)

    @property
    def buffer(self):
        return self._buffer

    @buffer.setter
    def buffer(self, buf: bytearray):
        self._buffer = buf
        for led in range(len(self)):
            self.led_colors[led] = tuple(buf[led*3+channel] for channel in self.GRB_CHANNEL_ORDER)
        self.flag_as_needing_rerender()

    def update(self, tick: int, dt: int, joysticks: dict):
        DummyLEDStrip.update(self)
