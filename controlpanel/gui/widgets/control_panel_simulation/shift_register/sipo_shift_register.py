import pygame as pg

from controlpanel.micropython_sdk.devices.base.shift_register import BaseSipoShiftRegister
from ....widgets import Widget
from artnet import ArtNet


class VirtualSipoShiftRegister(Widget, BaseSipoShiftRegister):
    SIZE = 16

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, count=1):
        super().__init__(name, parent, position[0], position[1], count*8*self.SIZE, self.SIZE, None)
        BaseSipoShiftRegister.__init__(self, artnet, name, count)
        self.rects = [pg.Rect(i*self.SIZE, 0, self.SIZE, self.SIZE) for i in range(count*8)]

    def parse_dmx_data(self, data: bytes):
        super().parse_dmx_data(data)
        self.flag_as_needing_rerender()

    def render_body(self):
        for rect, state in zip(self.rects, self._output_states):
            pg.draw.rect(self.surface, (255, 255, 255) if state else (0, 0, 0), rect)
