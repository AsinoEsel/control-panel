from ....widgets import Widget, Image
from controlpanel.shared.base.rotary_dial import BaseRotaryDial
import pygame as pg
from artnet import ArtNet


class VirtualRotaryDial(Image, BaseRotaryDial):
    ROTARY_DIAL_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/rotary_dial.png"
    SIZE = 30

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str):
        super().__init__(name, parent, position[0], position[1], self.ROTARY_DIAL_IMAGE_PATH, self.SIZE, self.SIZE)
        BaseRotaryDial.__init__(self, artnet, name)
        self.ms_since_last_input = 0

    def send_numbers(self):
        self.confirmed_numbers = self.entered_numbers[::]
        self.entered_numbers = []
        self.callback(self.confirmed_numbers)

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.TEXTINPUT:
            if event.text in [str(i) for i in range(10)]:
                self.entered_numbers.append(int(event.text))
                self.ms_since_last_input = 0
                if len(self.entered_numbers) >= 8:
                    self.send_numbers()
        super().handle_event(event)

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        self.ms_since_last_input += dt
        if self.ms_since_last_input > self.CONFIRMATION_TIME and self.entered_numbers:
            self.send_numbers()
