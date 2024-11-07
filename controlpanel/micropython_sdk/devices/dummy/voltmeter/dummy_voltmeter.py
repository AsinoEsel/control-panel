from ...base.voltmeter import BaseVoltmeter


class DummyVoltmeter(BaseVoltmeter):
    @property
    def duty(self) -> int:
        return self._duty

    @duty.setter
    def duty(self, value):
        if value != self._duty:
            print(f"setting duty to {value}")
            self._duty = value
            self.send_dmx_data()
