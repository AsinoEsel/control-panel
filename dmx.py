"""Adapted from https://github.com/maximecb/pyopendmx"""

import time
import random
import threading
from pyftdi.ftdi import Ftdi
import numpy as np

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
    def __init__(self, url='ftdi://ftdi:232:AL6E8JFW/1'):
        self.url = url
        self.port = Ftdi.create_from_url(url)
        self.port.reset()
        self.port.set_baudrate(baudrate=250000)
        self.port.set_line_property(bits=8, stopbit=2, parity='N', break_=False)
        assert self.port.is_connected

        # The 0th byte must be 0 (start code)
        # 513 bytes are sent in total
        self.data = bytearray(513 * [0])

        self.devices = []

    def __del__(self):
        self.port.close()

    def __setitem__(self, idx, val):
        assert (idx >= 1)
        assert (idx <= 512)
        assert isinstance(val, int)
        assert (val >= 0 and val <= 255)
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

    def add_device(self, device):
        # Check for partial channel overlaps between devices, which
        # are probably an error
        for other in self.devices:
            # Two devices with the same type and the same channel are probably ok
            if device.chan_no == other.chan_no and type(device) == type(other):
                continue

            if device.chan_overlap(other):
                raise Exception('partial channel overlap between devices "{}" and "{}"'.format(device.name, other.name))

        self.devices.append(device)
        return device

    def start_dmx_thread(self):
        """
        Thread to write channel data to the output port
        """

        def dmx_thread_fn():
            while True:
                for dev in self.devices:
                    dev.update(self)

                self.port.set_break(True)
                self.port.set_break(False)
                self.port.write_data(self.data)

                # The maximum update rate for the Enttec OpenDMX is 40Hz
                time.sleep(8/1000.0)

        dmx_thread = threading.Thread(target=dmx_thread_fn, args=(), daemon=True)
        dmx_thread.start()

class DMXDevice:
    def __init__(self, name, chan_no, num_chans):
        assert (chan_no >= 1)
        self.name = name
        self.chan_no = chan_no
        self.num_chans = num_chans

    def chan_overlap(this, that):
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
        self.dimming = 1.0
        self._strobe: int = 255
        self.strobe_frequency: float = 1.0
        self._yaw: float = 0.0
        self._pitch: float = -np.pi/4
        self._pan = 0
        self._tilt = 0.0
        self.speed = 1.0
        self._color: int = 0
        self._gobo1: int = 0
        self._gobo2: int = 0
        self._gobo2_rotation: int = 0
        self._prism: int = 0
        self.prism_speed: float = 0
        self.focus: float = 0.0
        self._pan_fine = 0
        self._tilt_fine = 0
        self.reset = 0
    
    def get_rgb(self):
        return self.COLORS[self.color]
    
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
    
    def next_color(self):
        if self.color < 30:
            self.color += 5
    
    def previous_color(self):
        if self.color >= 5:
            self.color -= 5

    def update(self, dmx: DMXUniverse):
        dmx.set_float(self.chan_no, 1, self.dimming)
        dmx.set_int(self.chan_no, 2, self._strobe)
        dmx.set_float(self.chan_no, 3, self._pan)
        dmx.set_float(self.chan_no, 4, self._tilt)
        dmx.set_float(self.chan_no, 5, 1 - self.speed)
        dmx.set_int(self.chan_no, 6, self._color)
        dmx.set_int(self.chan_no, 7, self._gobo1)
        dmx.set_int(self.chan_no, 8, self._gobo2)
        dmx.set_int(self.chan_no, 9, self._gobo2_rotation)
        dmx.set_int(self.chan_no, 10, self._prism)
        dmx.set_float(self.chan_no, 11, self.focus)
        dmx.set_float(self.chan_no, 12, self._pan_fine)
        dmx.set_float(self.chan_no, 13, self._tilt_fine)
        dmx.set_float(self.chan_no, 14, self.reset)
        

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


if __name__ == "__main__":
    import pygame as pg
    pg.init()
    screen = pg.display.set_mode((480,360))
    
    for device in Ftdi.list_devices():
        print(device)
    dmx = DMXUniverse(url='ftdi://0x403:0x6001:AL040AHB/1')

    moving_head = MovingHead(name="Moving Head", chan_no=1)
    dmx.add_device(moving_head)
    dmx.start_dmx_thread()
    
    moving_head.dimming = 0.1
    moving_head.speed = 1.0
    moving_head.pan = 0.0
    moving_head.tilt = 0.0
    moving_head.color = 0
    
    clock = pg.time.Clock()
    
    move_speed = 0.005

    while True:
        keys_pressed = pg.key.get_pressed()
        
        if keys_pressed[pg.K_a]:
            moving_head.pan += move_speed
        if keys_pressed[pg.K_d]:
            moving_head.pan -= move_speed
        if keys_pressed[pg.K_w]:
            moving_head.tilt += move_speed
        if keys_pressed[pg.K_s]:
            moving_head.tilt -= move_speed
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(10)