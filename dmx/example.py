from .dmx import DMXDevice, DMXUniverse, get_device_url
from .dmx_devices import MovingHead, VaritecColorsStarbar12
import pygame as pg


if __name__ == "__main__":
    dmx_universe = DMXUniverse(url=get_device_url(), devices=[MovingHead("Laser Cockpit", 1),
                                                          MovingHead("Laser Lichthaus", 15),
                                                          VaritecColorsStarbar12("Starbar Cockpit", 300),
                                                          ])

    
    pg.init()
    screen = pg.display.set_mode((480,360))
        
    color_bar: VaritecColorsStarbar12 = dmx_universe.devices.get("Starbar Cockpit")
    
    clock = pg.time.Clock()
    tick = 0
    
    while True:
        tick += 1
        
        light = tick % color_bar.LED_COUNT
        for i in range(color_bar.LED_COUNT):
            color_bar.lights[i] = 255 if i == light else 0
            color_bar.leds[i] = (255,0,0) if i == light else (0,0,0)
        
        print(color_bar.lights)
        
        for event in pg.event.get():
            ...
                    
                    
        
        keys_pressed = pg.key.get_pressed()
        
        if keys_pressed[pg.K_a]:
            dmx_universe.devices.get("WLED ESP")._effect -= 1
            print(dmx_universe.devices.get("WLED ESP")._effect)
        if keys_pressed[pg.K_d]:
            dmx_universe.devices.get("WLED ESP")._effect += 1
            print(dmx_universe.devices.get("WLED ESP")._effect)
        if keys_pressed[pg.K_w]:
            ...
        if keys_pressed[pg.K_s]:
            ...
        
        screen.fill((16,16,16))
        # color_bar.render(screen, position=pg.Vector2(10,10))
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(dmx_universe.target_frequency)