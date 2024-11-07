import pygame as pg
from controlpanel.micropython_sdk.devices.dummy.shift_register import DummyPisoSipoModule
from ....widgets import Widget
from artnet import ArtNet


class VirtualPisoSipoModule(Widget, DummyPisoSipoModule):
    SIZE = 16

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, callback, count=1):
        super().__init__(name, parent, position[0], position[1], count * 8 * self.SIZE, self.SIZE, None)
        DummyPisoSipoModule.__init__(self, artnet, name, count, callback=callback)
        self.rects = [pg.Rect(i * self.SIZE, 0, self.SIZE, self.SIZE) for i in range(count * 8)]

    def parse_dmx_data(self, data: bytes):
        DummyPisoSipoModule.parse_dmx_data(self, data)
        self.flag_as_needing_rerender()

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for rect in self.rects:
                if rect.collidepoint(event.pos[0] - self.position[0], event.pos[1] - self.position[1]):
                    index = self.rects.index(rect)
                    self._input_states[index] = not self._input_states[index]
                    self.callback(index, self._input_states[index])
                    self.flag_as_needing_rerender()
        super().handle_event(event)

    def render_body(self):
        for i in range(self._number_of_bits):
            pg.draw.rect(self.surface, (255, 255, 255) if self._output_states[i] else (0, 0, 0), self.rects[i])
            pg.draw.circle(self.surface, (0, 255, 0) if self._input_states[i] else (255, 0, 0), self.rects[i].center, self.SIZE//4)
