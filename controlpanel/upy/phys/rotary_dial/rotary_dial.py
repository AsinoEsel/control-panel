from machine import Pin
import time
from micropython import const
from controlpanel.shared.base.rotary_dial import BaseRotaryDial

DEBOUNCE_TIME = const(50)
DIGIT_CONFIRMATION_TIME = const(500)


class RotaryDial(BaseRotaryDial):
    def __init__(self, artnet, name: str, gpio_counter: int, gpio_reset: int):
        super().__init__(artnet, name)
        self.count: int = 0
        self.counter_switch = Switch(gpio_counter, trigger=self.increment_counter)
        self.reset_switch = Switch(gpio_reset, trigger=self.confirm_count)

    def confirm_count(self):
        if self.count == 0:
            return
        self.count %= 10
        self.send_trigger_data(self.count.to_bytes(1, "big"))
        self.count = 0

    def increment_counter(self):
        self.count = min(self.count + 1, 255)


class Switch:
    def __init__(self, gpio: int, trigger):
        self.trigger = trigger
        self.last_interrupt_time: int = 0
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self.switch_pressed)
    
    def switch_pressed(self, pin):
        if time.ticks_diff((current_time := time.ticks_ms()), self.last_interrupt_time) > DEBOUNCE_TIME:
            self.trigger()
            self.last_interrupt_time = current_time
