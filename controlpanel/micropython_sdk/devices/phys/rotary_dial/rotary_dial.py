from machine import Pin
import time
from micropython import const
import asyncio
from ...base.rotary_dial import BaseRotaryDial

DEBOUNCE_TIME = const(90)
DIGIT_CONFIRMATION_TIME = const(500)


class RotaryDial(BaseRotaryDial):
    def __init__(self, artnet, name: str, gpio_counter: int, gpio_reset: int, *, callback=None, confirmation_time: int | None = BaseRotaryDial.CONFIRMATION_TIME):
        super().__init__(artnet, name, callback=callback)
        self.count: int = 0
        self.counter_switch = Switch(gpio_counter, trigger=self.increment_counter)
        self.reset_switch = Switch(gpio_reset, trigger=self.confirm_count)
        self.confirmation_time = confirmation_time
    
    def get_status(self) -> tuple[bool, list[int]]:
        current_time = time.ticks_ms()
        last_interrupt_time = max(self.counter_switch.last_interrupt_time, self.reset_switch.last_interrupt_time)
        if time.ticks_diff(current_time, self.counter_switch.last_interrupt_time) > DIGIT_CONFIRMATION_TIME:
            self.confirm_count()
        if len(self.entered_numbers) >= 8:
            self.confirmed_numbers = self.entered_numbers[::]
            self.entered_numbers = []
            return True, self.confirmed_numbers
        if self.confirmation_time and time.ticks_diff(current_time, last_interrupt_time) > self.confirmation_time and (self.entered_numbers or self.count):
            self.confirm_count()
            self.confirmed_numbers = self.entered_numbers[::]
            self.entered_numbers = []
            return True, self.confirmed_numbers
        return False, self.entered_numbers
            
    def confirm_count(self):
        if self.count != 0:
            self.entered_numbers.append(self.count if self.count != 10 else 0)
            self.count = 0
        
    def increment_counter(self):
        self.count += 1

    def update(self):
        finished, numbers = self.get_status()
        if finished:
            self.callback(numbers)

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
    
    def get_payload(self) -> bytes:
        return bytes(self.confirmed_numbers)
    

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
