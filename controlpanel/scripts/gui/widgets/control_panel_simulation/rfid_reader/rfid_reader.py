from ....widgets import Widget, Image
from controlpanel.micropython_sdk.devices.base.rfid_reader import BaseRFIDReader
import pygame as pg
from artnet import ArtNet


class VirtualRFIDReader(Image, BaseRFIDReader):
    SIZE = 35
    RFID_READER_EMPTY_IMG_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/rfid_reader_empty.png"
    RFID_READER_CARD_IMG_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/rfid_reader_card.png"

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, callback):
        super().__init__(name, parent, position[0], position[1], self.RFID_READER_EMPTY_IMG_PATH, self.SIZE, self.SIZE)
        BaseRFIDReader.__init__(self, artnet, name, callback=callback)
        self.card_uid = None

    def get_uid(self) -> None | str:
        return self.card_uid

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        BaseRFIDReader.update(self)

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.card_uid = b"baddata"
            self.load_image(self.RFID_READER_CARD_IMG_PATH)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.card_uid = None
            self.load_image(self.RFID_READER_EMPTY_IMG_PATH)
        super().handle_event(event)
