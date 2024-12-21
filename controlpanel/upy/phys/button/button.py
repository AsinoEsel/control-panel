from machine import Pin
from controlpanel.shared.base.button import BaseButton
import time
import asyncio


class Button(BaseButton):
    def __init__(self, artnet, name: str, button_pin: int, *, invert=False) -> None:
        super().__init__(artnet, name)
        self.pin = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.invert = invert
        self.min_switch_delay: int = 10
        self.last_toggle_time: int = 0

    @property
    def state(self) -> int:
        return not self.pin.value() ^ self.invert

    async def run(self, updates_per_second):  # TODO: code review
        """
        Listens on pin value. Changes in this value cause callbacks.
        Prevents callbacks that happen too rapidly in succession (<min_switch_delay)
        """
        sleep_time = 1 / updates_per_second
        current_value = 0  # assume button is unpressed on boot

        while True:
            # skip iteration if nothing has changed
            old_value = current_value
            current_value = self.state
            if current_value == old_value:
                await asyncio.sleep(sleep_time)
                continue

            # skip iteration if value change appeared too soon
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, self.last_toggle_time) < self.min_switch_delay:
                await asyncio.sleep(sleep_time)
                continue
            self.last_toggle_time = current_time

            # valid value change causes callback
            self.send_trigger_data((self.state * 255).to_bytes(1, "big"))

            # wait before the next update
            await asyncio.sleep(sleep_time)
