from .dmx import DMXDevice, DMXUniverse
from pyftdi.ftdi import Ftdi
import numpy as np


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
                