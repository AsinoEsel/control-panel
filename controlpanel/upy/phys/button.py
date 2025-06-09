from machine import Pin
from controlpanel.shared.base.button import BaseButton
from .sensor import Sensor


class Button(BaseButton, Sensor):
    def __init__(self,
                 _artnet,
                 name: str,
                 pin: int,
                 *,
                 polling_rate_hz: float = 1.0,
                 invert: bool = False
                 ) -> None:
        Sensor.__init__(self, _artnet, name, polling_rate_hz)
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        # self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_interrupt)
        self._invert = invert
        self._previous_state: bool = self.get_pressed()

    def get_pressed(self) -> bool:
        return not self.pin.value() ^ self._invert

    async def update(self) -> None:
        current_state: bool = self.get_pressed()
        if current_state != self._previous_state:
            self._previous_state = current_state
            self.send_trigger(int(current_state).to_bytes(1, "big"))
