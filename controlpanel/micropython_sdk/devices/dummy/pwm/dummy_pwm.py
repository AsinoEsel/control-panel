from ...base.pwm import BasePWM


class DummyPWM(BasePWM):
    @property
    def duty(self) -> int:
        return self._duty

    @duty.setter
    def duty(self, value):
        if value != self._duty:
            self._duty = value
            self.send_dmx_data()
