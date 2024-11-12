from ....widgets import Widget, Image
from controlpanel.micropython_sdk.devices.base.water_flow_sensor import BaseWaterFlowSensor
import pygame as pg
from artnet import ArtNet


class VirtualWaterFlowSensor(Image, BaseWaterFlowSensor):
    SIZE = 50
    FLOW_RATES = [100, 70, 30, 5]
    EMPTY_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/water_flow_sensor_empty.png"
    FLOWING_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/water_flow_sensor_flowing.png"
    TRASH01_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/water_flow_sensor_trash01.png"
    TRASH02_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/water_flow_sensor_trash02.png"
    TRASH03_IMAGE_PATH = "controlpanel/scripts/gui/media/controlpanel_simulation/water_flow_sensor_trash03.png"
    TRASH_STAGES_PATHS = [EMPTY_IMAGE_PATH, TRASH01_IMAGE_PATH, TRASH02_IMAGE_PATH, TRASH03_IMAGE_PATH]

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], name: str, callback):
        super().__init__(name, parent, position[0], position[1], self.EMPTY_IMAGE_PATH, self.SIZE, self.SIZE)
        BaseWaterFlowSensor.__init__(self, artnet, name, callback=callback)
        self.flowing = False
        self.accumulated_dt = 0
        self.trash_level = 0

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.flowing = True
                self.load_image(self.FLOWING_IMAGE_PATH)
            if event.button == 3 and self.trash_level < 3:
                self.trash_level += 1
                self.load_image(self.TRASH_STAGES_PATHS[self.trash_level])
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.flowing = False
            self.load_image(self.TRASH_STAGES_PATHS[self.trash_level])
            self.flag_as_needing_rerender()
        return super().handle_event(event)

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        if self.flowing:
            self.flow_counter += int(self.FLOW_RATES[self.trash_level] * dt/1000)
        self.accumulated_dt += dt
        if self.accumulated_dt > 10_000:
            self.accumulated_dt = 0
            BaseWaterFlowSensor.update(self)
