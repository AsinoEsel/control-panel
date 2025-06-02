from controlpanel.shared.base.shift_register import BasePisoShiftRegister
from controlpanel.event_manager.dummy import SensorMixin


class PisoShiftRegister(BasePisoShiftRegister, SensorMixin):
    def parse_trigger_payload(self, data: bytes) -> tuple[str, tuple[tuple[int, bool], ...]]:
        # self._input_states = [byte for byte in data]  # TODO: Update dummy class
        updates: list[tuple[int, bool]] = []
        for i in range(0, len(data), 2):
            button_id: int = data[i]
            button_state: bool = not bool(data[i + 1])
            updates.append((button_id, button_state))

        return "ButtonsChanged", tuple(updates)
