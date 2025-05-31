from machine import Pin
from controlpanel.shared.base.button import BaseButton
from controlpanel.shared.mixins import PhysSensorMixin
import asyncio


class Button(BaseButton, PhysSensorMixin):
    def __init__(self, artnet, name: str, pin: int, *, invert: bool = False) -> None:
        super().__init__(artnet, name)
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        # self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_interrupt)
        self._state = self.pin.value() ^ invert
        self.invert = invert
        self.min_switch_delay: int = 10
        self.last_toggle_time: int = 0

    @property
    def state(self) -> int:
        return not self.pin.value() ^ self.invert

    async def _polling_loop(self, sleep_time_seconds: float):
        while True:
            await asyncio.sleep(sleep_time_seconds)
            current_state = self.pin.value() ^ self.invert

            if current_state != self._state:
                self._state = current_state
                self.send_trigger(current_state.to_bytes(1, "big"))
