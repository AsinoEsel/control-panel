from pyftdi.ftdi import Ftdi

def list_ftdi_devices():
    for device in Ftdi.list_devices():
        print(device)
        
list_ftdi_devices()


from dmx import *
import time

dmx = DMXUniverse(url='ftdi://0x403:0x6001:AL040AHB/1')

class ShehdsMovingHead(DMXDevice):
    """
    Moving head with RGBW and strobe.
    Modeled after the Docooler mini moving head
    CH1: motor pan
    CH2: motor tilt
    CH3: pan/tilt speed 0-255 (fast to slow)
    CH4: total dimming
    CH5: strobe speed
    CH6: R 0-255
    CH7: G 0-255
    CH8: B 0-255
    CH9: W 0-255

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

    def __init__(self, name, chan_no):
        super().__init__(name, chan_no, num_chans=12)
        self.pan = 0
        self.tilt = 0.5
        self.speed = .5
        self.dimming = 1.0
        self.rgbw = 0.5
        self.strobe = 1

    def update(self, dmx):
        dmx.set_float(self.chan_no, 1, self.dimming)
        dmx.set_float(self.chan_no, 2, self.strobe)
        dmx.set_float(self.chan_no, 3, self.pan)
        dmx.set_float(self.chan_no, 4, self.tilt)
        dmx.set_float(self.chan_no, 5, 1 - self.speed)
        dmx.set_float(self.chan_no, 6, self.rgbw)


moving_head = ShehdsMovingHead(name="Moving Head", chan_no=1)

dmx.add_device(moving_head)

dmx.start_dmx_thread()

while True:
    moving_head.tilt = 1
    time.sleep(1.5)
    moving_head.tilt = 0
    time.sleep(1.5)
