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
         Open Light     (251-255)
    CH3: Pan            (0-255)
    CH4: Tilt           (0-255)
    CH5: Pan/Tilt Speed (0-255)
    CH6: Color Wheel    (0-255)
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
    #phi_range = (0, 3*np.pi) # unused
    theta_range = (-100*np.pi/180, 100*np.pi/180)

    def __init__(self, name: str, chan_no: int):
        super().__init__(name, chan_no, num_chans=14)
        self.pan = 0
        self.tilt = 0.5
        self.speed = .5
        self.dimming = 1.0
        self.color = 0.5
        self.strobe = 1
        self.prism = 10

    def update(self, dmx):
        dmx.set_float(self.chan_no, 1, self.dimming)
        dmx.set_float(self.chan_no, 2, self.strobe)
        dmx.set_float(self.chan_no, 3, self.pan)
        dmx.set_float(self.chan_no, 4, self.tilt)
        dmx.set_float(self.chan_no, 5, 1 - self.speed)
        dmx.set_float(self.chan_no, 6, self.color)
        dmx.set_int(self.chan_no, 10, self.prism)
    
    def to_yaw_pitch(self) -> tuple[float, float]:
        if self.tilt < 0.5:
            return 3*np.pi*self.pan, abs(np.pi*(self.tilt-0.5))
        else:
            return np.pi*(3*self.pan+1), abs(np.pi*(self.tilt-0.5))


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