# EXPERIMENTAL

import pygame as pg
from pygame.event import Event
from .widget import Widget, Desktop
from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT, BACKGROUND_COLOR, DEFAULT_GAP
import dmx


class DMXMonitorDevice(Widget):
    def __init__(self, parent, x, y, w, h, device: dmx.DMXDevice) -> None:
        super().__init__(parent, x, y, w, h)
        self.device = device
        self.position = pg.Vector2(0,0)
    
    def render(self):
        raise NotImplementedError


class VaritecColorsStarbar12(DMXMonitorDevice):
    def __init__(self, parent, x, y, w, h, device: dmx.VaritecColorsStarbar12) -> None:
        super().__init__(parent, x, y, w, h, device)
    
    def handle_event(self, event: Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_a:
                self.device.function -= 1
                print(self.device.function, self.device._function)
            elif event.key == pg.K_d:
                self.device.function += 1
                print(self.device.function, self.device._function)
            elif event.key == pg.K_w:
                self.device.effect_speed += 0.1
                print(self.device.effect_speed)
            elif event.key == pg.K_s:
                self.device.effect_speed -= 0.1
                print(self.device.effect_speed)
        super().handle_event(event)
        
    def render(self):
        print("rne")
        led_width = 30
        width = self.device.LED_COUNT * led_width
        height = 30
        light_radius = led_width // 4
        for i, led in enumerate(self.device.leds):
            pg.draw.rect(self.surface, led, pg.Rect(self.position.x + i*led_width, self.position.y, led_width, height))
        for i, light in enumerate(self.device.lights):
            pg.draw.circle(self.surface, (light, light, 0.8*light), self.position+pg.Vector2(i*led_width + led_width//2, height//2), light_radius)
        pg.draw.rect(self.surface, (64,64,64), pg.Rect(self.position.x, self.position.y, width, led_width), 2)


class DMXMonitor(Widget):
    def __init__(self, parent, x, y, w, h) -> None:
        super().__init__(parent, x, y, w, h)
        for i, device in enumerate(dmx.dmx_universe.devices.values()):
            if isinstance(device, dmx.VaritecColorsStarbar12):
                self.elements.append(VaritecColorsStarbar12(self, DEFAULT_GAP, DEFAULT_GAP + i*50, w-2*DEFAULT_GAP, 50, device))

if __name__ == "__main__":
    from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT, RENDER_SIZE
    import asyncio
    pg.init()
    screen = pg.display.set_mode(RENDER_SIZE)
    
    dmx_monitor = DMXMonitor(None, 0, 0, RENDER_WIDTH, RENDER_HEIGHT)
    
    running = True
    clock = pg.time.Clock()
    tick=0
    while running:
        tick += 1
        
        
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False
            dmx_monitor.handle_event(event)
        
        dmx_monitor.propagate_update(tick=0, dt=0, joysticks={})
        screen.blit(dmx_monitor.surface, (0,0))
                                        
        pg.display.flip()
        pg.event.pump()
        clock.tick(60)