from machine import Pin
from controlpanel.shared.base.button import BaseButton
from .sensor import Sensor
from controlpanel.shared.compatibility import const
from time import ticks_ms, ticks_diff


_DEBOUNCE_MS = const(5)


class Button(BaseButton, Sensor):
    def __init__(self,
                 _artnet,
                 name: str,
                 pin: int,
                 *,
                 update_rate_hz: float = 1.0,
                 invert: bool = False
                 ) -> None:
        Sensor.__init__(self, _artnet, name, update_rate_hz)
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_interrupt)
        self._invert = invert
        self._previous_state: bool = self.get_pressed()
        self._last_interrupt_time: int = 0

    def _handle_interrupt(self, pin: Pin) -> None:
        current_time = ticks_ms()
        if ticks_diff(current_time, self._last_interrupt_time) < _DEBOUNCE_MS:
            return
        self._last_interrupt_time = current_time
        current_state: bool = self.get_pressed()
        if current_state != self._previous_state:
            self._previous_state = current_state
            print(f"sending trigger via interrupt {current_state}")
            self._send_trigger_packet(int(current_state).to_bytes(1, "big"))


    def get_pressed(self) -> bool:
        return not self.pin.value() ^ self._invert

    async def update(self) -> None:
        current_state: bool = self.get_pressed()
        if current_state != self._previous_state:
            self._previous_state = current_state
            print(f"sending trigger {current_state}")
            self._send_trigger_packet(int(current_state).to_bytes(1, "big"))
