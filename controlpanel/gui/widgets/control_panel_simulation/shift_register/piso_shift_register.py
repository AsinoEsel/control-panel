import pygame as pg
from controlpanel.shared.base.shift_register import BasePisoShiftRegister
from ....widgets import Widget
from artnet import ArtNet


class VirtualPisoShiftRegister(Widget, BasePisoShiftRegister):
    SIZE = 16

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, count=1):
        super().__init__(name, parent, position[0], position[1], count*8*self.SIZE, self.SIZE, None)
        BasePisoShiftRegister.__init__(self, artnet, name, count)
        self.rects = [pg.Rect(i*self.SIZE, 0, self.SIZE, self.SIZE) for i in range(count*8)]

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        pass

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for rect in self.rects:
                if rect.collidepoint(event.pos[0] - self.position[0], event.pos[1] - self.position[1]):
                    index = self.rects.index(rect)
                    self._input_states[index] = not self._input_states[index]
                    print(index, self._input_states)
                    self.callback(index, self._input_states[index])
                    self.flag_as_needing_rerender()
        super().handle_event(event)

    def render_body(self):
        for rect, state in zip(self.rects, self._input_states):
            pg.draw.rect(self.surface, (255, 255, 255) if state else (0, 0, 0), rect)
