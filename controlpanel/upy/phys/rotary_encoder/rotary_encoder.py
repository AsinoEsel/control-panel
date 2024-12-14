from .rotary_irq_esp import RotaryIRQ
from controlpanel.shared.base.sensor import Sensor


class RotaryEncoder(Sensor, RotaryIRQ):
    SUBKEY = 1

    def __init__(self, artnet, name: str, pin_num_clk: int, pin_num_dt: int, callback):
        super().__init__(artnet, name)
        RotaryIRQ.__init__(self, pin_num_clk, pin_num_dt, 0, 255, range_mode=RotaryIRQ.RANGE_WRAP, reverse=True)
        self.name = name
        self.add_listener(self.wrapper_callback)
        self.callback = callback
    
    def wrapper_callback(self):
        self.callback(self.direction)
    