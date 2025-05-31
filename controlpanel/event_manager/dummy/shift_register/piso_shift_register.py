from controlpanel.shared.base.shift_register import BasePisoShiftRegister


class PisoShiftRegister(BasePisoShiftRegister):
    def parse_trigger_data(self, data: bytes) -> tuple[str, tuple[tuple[int, bool]]]:
        # self._input_states = [byte for byte in data]  # TODO: Update dummy class
        updates = []
        for i in range(0, len(data), 2):
            button_id = data[i]
            button_state = not bool(data[i + 1])
            updates.append((button_id, button_state))

        return "ButtonsChanged", tuple(updates)
