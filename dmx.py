"""Adapted from https://github.com/maximecb/pyopendmx"""

import time
import random
import threading
from pyftdi.ftdi import Ftdi
import numpy as np
import pygame as pg

def random_rgb():
    while True:
        color = np.array([
            random.choice([1, 0]),
            random.choice([1, 0]),
            random.choice([1, 0]),
        ])

        if color.any():
            break

    return color

def random_rgbw():
    while True:
        color = np.array([
            random.choice([1, 0]),
            random.choice([1, 0]),
            random.choice([1, 0]),
            random.choice([1, 0]),
        ])

        if color.any():
            break

    return color

def map_to(val, min, max):
    assert max > min
    val = np.clip(val, 0, 1)
    return int(round(min + val * (max - min)))

class DMXUniverse:
    """
    Interface to an ENTTEC OpenDMX (FTDI) DMX interface
    """
    def __init__(self, url: str|None, devices: list['DMXDevice']|None = None, *, target_frequency: int = 20):
        self.target_frequency = target_frequency  # In Hz
        # The 0th byte must be 0 (start code)
        # 513 bytes are sent in total
        self.data = bytearray(513 * [0])
        
        self.devices: dict[str:'DMXDevice'] = {}
        if devices is None:
            devices = []
        for device in devices:
            self.add_device(device)
            
        if url:
            self.url = url
            self.port = Ftdi.create_from_url(url)
            self.port.reset()
            self.port.set_baudrate(baudrate=250000)
            self.port.set_line_property(bits=8, stopbit=2, parity='N', break_=False)
            assert self.port.is_connected
            self.start_dmx_thread()
            print(f"Successfully initiated a DMX universe @ {url}.")
        else:
            print("Was unable to initiate DMX Universe. (No devices found)")


    def __del__(self):
        self.port.close()

    def __setitem__(self, idx, val):
        assert (1 <= idx <= 512)
        assert isinstance(val, int)
        assert (0 <= val <= 255)
        self.data[idx] = val

    def set_int(self, start_chan, chan_no, int_val):
        self[start_chan + chan_no - 1] = int_val

    def set_float(self, start_chan, chan_no, val, min=0, max=255):
        assert (chan_no >= 1)

        # If val is an array of values
        if hasattr(val, '__len__'):
            for i in range(len(val)):
                int_val = map_to(val[i], min, max)
                self[start_chan + chan_no - 1 + i] = int_val
        else:
            int_val = map_to(val, min, max)
            self[start_chan + chan_no - 1] = int_val

    def add_device(self, device: 'DMXDevice'):
        # Check if name is already in use:
        if self.devices.get(device.name):
            raise Exception('Device name {} already in use.'.format(device.name))
        
        # Check for partial channel overlaps between devices, which
        # are probably an error
        for other in self.devices.values():
            # Two devices with the same type and the same channel are probably ok
            if device.chan_no == other.chan_no and type(device) == type(other):
                continue

            if device.chan_overlap(other):
                raise Exception('partial channel overlap between devices "{}" and "{}"'.format(device.name, other.name))

        self.devices[device.name] = device
        return device

    def start_dmx_thread(self):
        """
        Thread to write channel data to the output port
        """

        def dmx_thread_fn():
            target_interval = 1.0/self.target_frequency # The maximum update rate for the Enttec OpenDMX is 40Hz
            
            while True:
                start_time = time.time()  # Get the current time at the start of the loop
                
                for dev in self.devices.values():
                    dev.update(self)

                self.port.set_break(True)
                self.port.set_break(False)
                self.port.write_data(self.data)

                elapsed_time = time.time() - start_time
                sleep_time = max(0, target_interval - elapsed_time)
                if sleep_time == 0:
                    print("Warning: DMX thread could not keep up with target frequency. If this warning appears often, consider lowering it.")
                time.sleep(sleep_time)

        dmx_thread = threading.Thread(target=dmx_thread_fn, args=(), daemon=True)
        dmx_thread.start()

class DMXDevice:
    def __init__(self, name: str, chan_no: int, num_chans: int):
        assert (chan_no >= 1)
        self.name = name
        self.chan_no = chan_no
        self.num_chans = num_chans

    def chan_overlap(this, that: 'DMXDevice'):
        """
        Check if two devices have overlapping channels
        """

        this_last = this.chan_no + (this.num_chans - 1)
        that_last = that.chan_no + (that.num_chans - 1)

        return (
            (this.chan_no >= that.chan_no and this.chan_no <= that_last) or
            (that.chan_no >= this.chan_no and that.chan_no <= this_last)
        )

    def update(self, dmx):
        raise NotImplementedError

class MovingHead(DMXDevice):
    """
    Moving head.
    Modeled after the Shehds "LED Spot 100W Lighting" moving head
    CH1: Dimming        (0-255)
    CH2: Strobe Speed   (4-251)
         Open Light     (252-255)
    CH3: Pan            (0-255)
    CH4: Tilt           (0-255)
    CH5: Pan/Tilt Speed (0-255)
    CH6: Color          (0-255)
         White:         0-4
         Red:           5-9
         Green:         10-14
         Blue:          15-19
         Yellow:        20-24
         Purple:        25-29
         Cyan:          30-34
    CH7: Gobo 1
    CH8: Gobo 2
    CH9: Gobo 2 Rotation
    CH10: Prism Switch  (10-14)
          Prism Rot.    (15-255)
    CH11: Focus         (0-255)
    CH12: Pan fine      (0-255)
    CH13: Tilt fine     (0-255)
    CH14: Reset         (255)

    Pan:
    0.00 is pointing back
    0.15 is pointing left
    0.33 is pointing forward
    0.50 is pointing right

    Tilt:
    0.00 is pointing forward
    0.50 is fully up
    1.00 is pointing back
    """
    THETA_RANGE = (-95*np.pi/180, -5*np.pi/180)
    NUM_COLORS = 7
    NUM_GOBOS1 = 8
    NUM_GOBOS2 = 7
    BEAM_ANGLE = 16
    COLORS = {0: (255,255,255),
              1: (255,0,0),
              2: (0,255,0),
              3: (0,0,255),
              4: (255,255,0),
              5: (255,0,255),
              6: (0,255,255),
              }

    def __init__(self, name: str, chan_no: int):
        super().__init__(name, chan_no, num_chans=14)
        self._intensity: float = 1.0
        self._strobe: int = 255
        self._pan: float = 0.0
        self._tilt: float = 0.0
        self._speed: float = 1.0
        self._color: int = 0
        self._gobo1: int = 0
        self._gobo2: int = 0
        self._gobo2_rotation: int = 0
        self._prism: int = 0
        self._focus: float = 0.0
        self._pan_fine: float = 0.0
        self._tilt_fine: float = 0.0
        self._reset: float = 0.0
        
        self._yaw: float = 0.0
        self._pitch: float = -np.pi/4
        self.strobe_frequency: float = 1.0
        self.prism_speed: float = 0
    
    def get_rgb(self):
        return self.COLORS[self.color]
    
    def reset(self):
        self._reset = 1.0
    
    @property
    def intensity(self):
        return self._intensity
    
    @intensity.setter
    def intensity(self, value: float):
        self._intensity = min(1.0, max(0.0, value))
    
    @property
    def yaw(self) -> float:
        return self._yaw
    
    @yaw.setter
    def yaw(self, radians: float):
        angle = radians % (2*np.pi)
        self._yaw = angle
        self._pan = angle / (3*np.pi)
        if self._pan > 5/6:
            self._pan -= 4/6
        elif self._pan < 1/6:
            self._pan += 4/6
        # self._pan = int(angle)
        # self._pan_fine = angle - int(angle)
    
    @property
    def pitch(self) -> float:
        return self._pitch
    
    @pitch.setter
    def pitch(self, radians: float):
        angle = max(min(self.THETA_RANGE[1], radians), self.THETA_RANGE[0])
        self._pitch = angle
        self._tilt = angle/np.pi + 1/2
        #self._tilt = angle
        # self._tilt = int(angle)
        # self._tilt_fine = angle - int(angle)
    
    @property
    def speed(self):
        return self._speed
    
    @speed.setter
    def speed(self, value: float):
        self._speed = min(1.0, max(0.0, value))
        
    @property
    def prism(self):
        return True if self._prism >= 10 else False
    
    @prism.setter
    def prism(self, value: bool):
        if value is True:
            self._prism = 15 + int(240*self.prism_speed)
        elif value is False:
            self._prism = 0
    
    @property
    def strobe(self):
        return True if self._strobe <= 251 else False
    
    @strobe.setter
    def strobe(self, value: bool):
        if value is True:
            self._strobe = 4 + int(247*self.strobe_frequency)
        elif value is False:
            self._strobe = 255
    
    @property
    def color(self):
        return self._color // 5
    
    @color.setter
    def color(self, value: int):
        self._color = 5*(value % self.NUM_COLORS)
    
    @property
    def gobo1(self):
        return self._gobo1 // 10
    
    @gobo1.setter
    def gobo1(self, value: int):
        self._gobo1 = 10*(value % self.NUM_GOBOS1)
    
    @property
    def gobo2(self):
        return self._gobo2 // 10
    
    @gobo2.setter
    def gobo2(self, value: int):
        self._gobo2 = 10*(value % self.NUM_GOBOS2)
        
    @property
    def gobo2_rotation(self):
        return self._gobo2_rotation
    
    @gobo2_rotation.setter
    def gobo2_rotation(self, value: float):
        if value == 0:
            self._gobo2_rotation = 0
        elif value > 0:
            self._gobo2_rotation = 64 + int((127-64)*value)
        elif value < 0:
            self._gobo2_rotation = 255 - int(65 * (value+1))
    
    @property
    def focus(self):
        return self._focus
    
    @focus.setter
    def focus(self, value: float):
        self._focus = min(1.0, max(0.0, value))
    
    def next_color(self):
        if self.color < 30:
            self.color += 5
    
    def previous_color(self):
        if self.color >= 5:
            self.color -= 5

    def update(self, dmx: DMXUniverse):
        dmx.set_float(self.chan_no, 1, self._intensity)
        dmx.set_int(self.chan_no, 2, self._strobe)
        dmx.set_float(self.chan_no, 3, self._pan)
        dmx.set_float(self.chan_no, 4, self._tilt)
        dmx.set_float(self.chan_no, 5, 1 - self._speed)
        dmx.set_int(self.chan_no, 6, self._color)
        dmx.set_int(self.chan_no, 7, self._gobo1)
        dmx.set_int(self.chan_no, 8, self._gobo2)
        dmx.set_int(self.chan_no, 9, self._gobo2_rotation)
        dmx.set_int(self.chan_no, 10, self._prism)
        dmx.set_float(self.chan_no, 11, self._focus)
        dmx.set_float(self.chan_no, 12, self._pan_fine)
        dmx.set_float(self.chan_no, 13, self._tilt_fine)
        dmx.set_float(self.chan_no, 14, self._reset)


class VaritecColorsStarbar12(DMXDevice):
    LED_COUNT = 12
    FUNCTIONS = [int((255/64)*i)+7 for i in range(62)]
    def __init__(self, name: str, chan_no: int):
        super().__init__(name, chan_no, num_chans=52)
        self.intensity: float = 1.0
        self.strobe: float = 0.0
        self.leds: list[tuple[int,int,int]] = [(0,0,0) for _ in range(self.LED_COUNT)]
        self.lights: list[int] = [0 for _ in range(self.LED_COUNT)]
        self._function: int = 7
        self.effect_speed: float = 0.5
    
    def render(self, surface: pg.Surface, position: pg.Vector2 = pg.Vector2(0,0)):
        led_width = 30
        width = self.LED_COUNT * led_width
        height = 30
        light_radius = led_width // 4
        for i, led in enumerate(self.leds):
            pg.draw.rect(surface, led, pg.Rect(position.x + i*led_width, position.y, led_width, height))
        for i, light in enumerate(self.lights):
            pg.draw.circle(surface, (light, light, 0.8*light), position+pg.Vector2(i*led_width + led_width//2, height//2), light_radius)
        pg.draw.rect(surface, (64,64,64), pg.Rect(position.x, position.y, width, led_width), 2)
    
    @property
    def function(self):
        return int(self._function / (255/64)) - 1
    
    @function.setter
    def function(self, value: int):
        
        self._function = int(self.FUNCTIONS[value]) if 0<=value<len(self.FUNCTIONS) else 7
    
    def update(self, dmx: DMXUniverse):
        dmx.set_float(self.chan_no, 1, self.intensity)
        dmx.set_float(self.chan_no, 2, self.strobe)
        for i in range(self.LED_COUNT):
            dmx.set_int(self.chan_no, 3 + i*4 + 0, self.leds[i][0])
            dmx.set_int(self.chan_no, 3 + i*4 + 1, self.leds[i][1])
            dmx.set_int(self.chan_no, 3 + i*4 + 2, self.leds[i][2])
            dmx.set_int(self.chan_no, 3 + i*4 + 3, self.lights[i])
        dmx.set_int(self.chan_no, 51, self._function)
        dmx.set_float(self.chan_no, 52, self.effect_speed)
                

def get_device_url() -> str|None:
    devices = Ftdi.list_devices()
    if not devices:
        return None
    else:
        device = devices[0]
        vid = hex(device[0].vid)
        pid = hex(device[0].pid)
        sn = device[0].sn
        return f'ftdi://{vid}:{pid}:{sn}/1'


dmx_universe = DMXUniverse(url=get_device_url(), devices=[MovingHead("Laser Cockpit", 1),
                                                          MovingHead("Laser Lichthaus", 15),
                                                          VaritecColorsStarbar12("Starbar Cockpit", 300)])


if __name__ == "__main__":
    pg.init()
    screen = pg.display.set_mode((480,360))
    
    #dmx_universe.add_device(color_bar := VaritecColorsStarbar12("VaritecColorsStarbar12", 300))
    
    color_bar: VaritecColorsStarbar12 = dmx_universe.devices["Starbar Cockpit"]
    
    clock = pg.time.Clock()
    tick = 0
    
    while True:
        tick += 1
        light = tick % color_bar.LED_COUNT
        for i in range(color_bar.LED_COUNT):
            color_bar.lights[i] = 255 if i == light else 0
            color_bar.leds[i] = (255,0,0) if i == light else (0,0,0)
        
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_a:
                    color_bar.function -= 1
                    print(color_bar.function, color_bar._function)
                elif event.key == pg.K_d:
                    color_bar.function += 1
                    print(color_bar.function, color_bar._function)
                elif event.key == pg.K_w:
                    color_bar.effect_speed += 0.1
                    print(color_bar.effect_speed)
                elif event.key == pg.K_s:
                    color_bar.effect_speed -= 0.1
                    print(color_bar.effect_speed)
                    
                    
        
        keys_pressed = pg.key.get_pressed()
        
        if keys_pressed[pg.K_a]:
            ...
        if keys_pressed[pg.K_d]:
            ...
        if keys_pressed[pg.K_w]:
            ...
        if keys_pressed[pg.K_s]:
            ...
        
        screen.fill((16,16,16))
        color_bar.render(screen, position=pg.Vector2(10,10))
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(dmx_universe.target_frequency)