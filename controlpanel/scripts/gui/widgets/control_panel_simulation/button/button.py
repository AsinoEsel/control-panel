from ....widgets import Widget, Image
from controlpanel.micropython_sdk.devices.dummy.button import DummyButton
import pygame as pg
from artnet import ArtNet


class VirtualButton(Image, DummyButton):
    ACTIVE_STATE_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/button_pressed.png"
    INACTIVE_STATE_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/button_unpressed.png"

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, callback=None) -> None:
        super().__init__(name, parent, position[0], position[1], self.INACTIVE_STATE_IMAGE_PATH)
        DummyButton.__init__(self, artnet, name, callback=callback)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        if val != self.state:
            self._state = val
            self.load_image(self.ACTIVE_STATE_IMAGE_PATH if self.state else self.INACTIVE_STATE_IMAGE_PATH)
            self.callback(self.state)

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.state = 1
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.state = 0
        return super().handle_event(event)


class VirtualSwitch(VirtualButton):
    ACTIVE_STATE_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/switch_flipped.png"
    INACTIVE_STATE_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/switch_unflipped.png"

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.state = int(not self.state)
        return Widget.handle_event(self, event)
