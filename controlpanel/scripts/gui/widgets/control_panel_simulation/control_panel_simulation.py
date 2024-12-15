import pygame as pg
from ...widgets import Widget, Desktop
from controlpanel.scripts.gui.window_manager.window_manager_setup import BACKGROUND_COLOR
from controlpanel.shared import base
from artnet import ArtNet


from .button import VirtualSwitch
from .led_strip import VirtualLEDStrip
from .pwm import VirtualLED
from .voltmeter import VirtualVoltmeter
from .water_flow_sensor import VirtualWaterFlowSensor
from .rotary_dial import VirtualRotaryDial
from .rfid_reader import VirtualRFIDReader
from .seven_segment_display import VirtualSevenSegmentDisplay

from .shift_register import VirtualSipoShiftRegister, VirtualPisoShiftRegister, VirtualPisoSipoModule
from .control_panel import VirtualBVGPanel, VirtualBananaPlugs


class ESP:
    def __init__(self, name: str, elements: list[base.Fixture | base.Sensor]) -> None:
        self.name = name
        self.elements = elements


class ControlPanelSimulation(Widget):
    def __init__(self, name: str, parent: Widget | Desktop, artnet: ArtNet, x=None, y=None, w=None, h=None) -> None:

        test_led_strip = VirtualLEDStrip(artnet, self, (50, 20), "TestLEDStrip", 30)
                                         # animation=base.led_strip.animations.looping_line(30, 0.2, (255, 255, 255), (0, 0, 0), 1000))
        test_button = VirtualSwitch(artnet, self, (20, 20), "TestButton")
        test_pwm = VirtualLED(artnet, self, (100, 50), "TestPWM", (255, 0, 0))  # lambda t: abs(sin(t / 1000))
        test_voltmeter = VirtualVoltmeter(artnet, self, (200, 300), "TestVoltmeter", noise_intensity=0.1)  # lambda t: abs(sin(t / 3000))
        test_waterflowsensor = VirtualWaterFlowSensor(artnet, self, (250, 50), "TestWaterFlowSensor")  # lambda water: print(water)
        test_rotarydial = VirtualRotaryDial(artnet, self, (200, 200), "TestRotaryDial")  # lambda numbers: print(numbers)
        test_sevensegmentdisplay = VirtualSevenSegmentDisplay(artnet, self, (300, 250), "TestSevenSegmentDisplay", 16)
        test_rfidreader = VirtualRFIDReader(artnet, self, (20, 300), "TestRFIDReader")  # lambda uid: print(uid)
        test_siposhiftregister = VirtualSipoShiftRegister(artnet, self, (200, 400), "TestSipoShiftRegister", 1)
        test_pisoshiftregister = VirtualPisoShiftRegister(artnet, self, (200, 450), "TestPisoShiftRegister", 2)
        test_pisosipomodule = VirtualPisoSipoModule(artnet, self, (200, 500), "TestPisoSipoModule", 2)
        test_bvgpanel = VirtualBVGPanel(artnet, self, (400, 300), "TestBVGPanel")
        test_bananaplugs = VirtualBananaPlugs(artnet, self, (600, 50), 4, 6, "TestBananaPlugs")

        self.esps = [ESP("test", elements=[test_button, test_led_strip, test_pwm, test_voltmeter,
                                           test_waterflowsensor, test_rotarydial, test_sevensegmentdisplay,
                                           test_rfidreader, test_siposhiftregister, test_pisoshiftregister,
                                           test_pisosipomodule, test_bvgpanel, test_bananaplugs])]

        self.wireframe_image_surface = pg.image.load("controlpanel/scripts/gui/media/controlpanel_simulation/controlpanel_wireframe.png")

        elements = []
        for esp in self.esps:
            for element in esp.elements:
                elements.append(element)

        super().__init__(name, parent, x, y, w, h, elements)

    def render_body(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.surface.blit(self.wireframe_image_surface, (0, 0))
