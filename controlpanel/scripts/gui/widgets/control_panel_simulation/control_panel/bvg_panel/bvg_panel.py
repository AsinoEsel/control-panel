from controlpanel.scripts.gui.widgets import Widget
import pygame as pg
from controlpanel.micropython_sdk.devices.dummy.control_panel import DummyBVGPanel
from dataclasses import dataclass
from artnet import ArtNet


class VirtualBVGPanel(Widget, DummyBVGPanel):
    WIDTH = 486
    HEIGHT = 224

    RED_ON = (255, 0, 0)
    RED_OFF = (32, 0, 0)
    YELLOW_ON = (255, 255, 0)
    YELLOW_OFF = (32, 32, 0)
    GREEN_ON = (0, 255, 0)
    GREEN_OFF = (0, 32, 0)

    GRAY = (60, 60, 60)

    @dataclass
    class Button:
        rect: pg.Rect
        color_on: tuple[int, int, int]
        color_off: tuple[int, int, int]
        toggle: bool

    @dataclass
    class LED:
        position: tuple[int, int]
        color_on: tuple[int, int, int]
        color_off: tuple[int, int, int]

    def __init__(self, artnet: ArtNet, parent, position: tuple[int, int], name: str):
        super().__init__(name, parent, position[0], position[1], self.WIDTH, self.HEIGHT, None)
        DummyBVGPanel.__init__(self, artnet, name)
        self.buttons = []
        self.buttons.extend([self.Button(pg.Rect(16 + i * 22, 16, 20, 20), self.RED_ON, self.RED_OFF, True if i in (3,4,5) else False) for i in range(9)])
        self.buttons.extend([self.Button(pg.Rect(16 + i * 22, 98 + j * 32, 20, 20), self.YELLOW_ON, self.YELLOW_OFF, True if i in (0,1,2,8) else False) for j in range(3) for i in range(9)])
        self.buttons.append(self.Button(pg.Rect(367, 98, 20, 20), self.YELLOW_ON, self.YELLOW_OFF, False))
        self.buttons.extend([self.Button(pg.Rect(345 + i * 22, 130, 20, 20), self.YELLOW_ON, self.YELLOW_OFF, True if i == 0 else False) for i in range(2)])
        self.buttons.extend([self.Button(pg.Rect(345 + i * 22, 162, 20, 20), self.YELLOW_ON, self.YELLOW_OFF, True if i == 0 else False) for i in range(2)])
        self.buttons.append(self.Button(pg.Rect(433, 30, 20, 20), self.YELLOW_ON, self.YELLOW_OFF, True))
        self.buttons.extend([self.Button(pg.Rect(455, 30 + i * 33, 20, 20), self.GREEN_ON, self.GREEN_OFF, True) for i in range(5)])
        self.leds = []
        self.leds.extend([self.LED((224 + i * 22, 26), self.RED_ON, self.RED_OFF) for i in range(7)])
        self.leds.extend([self.LED((224 + i * 22, 108 + j * 32), self.GREEN_ON, self.GREEN_OFF) for i in range(6) for j in range(3)])
        self.address_rect = pg.Rect(348, 90, 16, 27)
        self.address_font = pg.font.Font("controlpanel/scripts/gui/media/clacon2.ttf", 36)

    def parse_dmx_data(self, data: bytes):
        super().parse_dmx_data(data)
        self.flag_as_needing_rerender()

    def render_body(self):
        self.surface.fill(self.GRAY)
        for i, button in enumerate(self.buttons):
            pg.draw.rect(self.surface, button.color_on if self._output_states[i] else button.color_off, button.rect)
            if self._input_states[i]:
                pg.draw.rect(self.surface, (255, 255, 255), button.rect, 1)
        for i, led in enumerate(self.leds):
            pg.draw.circle(self.surface, led.color_on if self._output_states[len(self.buttons)+i] else led.color_off, led.position, 5)
        pg.draw.rect(self.surface, (0, 0, 0), self.address_rect)
        self.surface.blit(self.address_font.render(str(self.address), True, (255, 255, 255), (0, 0, 0)), self.address_rect)

    def get_button_at_position(self, pos: tuple[int, int]) -> Button:
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                return button

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            relative_event_pos = (event.pos[0] - self.position[0], event.pos[1] - self.position[1])
            if event.button == 1:
                if button := self.get_button_at_position(relative_event_pos):
                    index = self.buttons.index(button)
                    if button.toggle:
                        self._input_states[index] = not self._input_states[index]
                    else:
                        self._input_states[index] = True
                    self.send_button_data(index, self._input_states[index])
                    self.send_data()
                elif self.address_rect.collidepoint(relative_event_pos):
                    self.address = (self.address + 1) % 10
                    self.send_address_data(self.address)
            elif event.button == 3:
                if self.address_rect.collidepoint(relative_event_pos):
                    self.address = (self.address - 1 + 10) % 10
                    self.send_address_data(self.address)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            relative_event_pos = (event.pos[0] - self.position[0] - 6, event.pos[1] - self.position[1] - 6)  # obscure pygame bug requires subtracting (6,6)
            if button := self.get_button_at_position(relative_event_pos):
                index = self.buttons.index(button)
                if not button.toggle:
                    self._input_states[index] = False
                    self.send_button_data(index, self._input_states[index])
                    self.send_data()
                    # self.flag_as_needing_rerender()

        super().handle_event(event)
