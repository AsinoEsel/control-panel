from controlpanel.shared.base.bvg_panel import BaseBVGPanel
from controlpanel.upy.phys.shift_register import PisoSipoModule
import asyncio


class BVGPanel(PisoSipoModule, BaseBVGPanel):
    PISO_REMAPPING = [35, 16, 17, 8, None, None, None, None, None, None, None, None, None, None, None, None,
                      7, 6, 5, 4, 3, 2, 1, 0, 16, 15, 14, 13, 12, 11, 10, 9,
                      25, 34, 24, 33, 23, 32, 22, 31, 21, 30, 20, 29, 19, 28, 18, 27,
                      42, 41, 43, 44, 36, None, None, None, None, None, 45, 38, 37, 46, 40, 39,
                      None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
    SIPO_REMAPPING = [1, 3, 5, 7, 9, 11, 13, 15, 49, 0, 2, 4, 6, 8, 10, 12,
                      14, 57, 17, 21, 19, 23, 25, 27, 29, 31, 46, 16, 18, 20, 22, 24,
                      26, 28, 30, 47, None, 69, 76, 79, 78, None, None, 72, None, None, None, 50,
                      51, 52, 53, 54, 55, 56, 58, 59, 60, 61, 62, 63, 44, 41, 39, 37,
                      35, 33, 45, 42, 40, 38, 36, 34, None, None, None, None, None, None, None, None]
    ADDRESS_PINS = [57, 56, 55, 53]

    def __init__(
            self,
            artnet,
            name: str,
            clock: int,
            latch: int,
            serial_in: int,
            serial_out: int,
            *,
            universe: list[int] | None = None,
    ):

        super().__init__(artnet,
                         name,
                         clock,
                         latch,
                         serial_in,
                         serial_out,
                         BaseBVGPanel.SHIFT_REGISTER_COUNT,
                         universe=universe,
                         piso_remapping=self.PISO_REMAPPING,
                         sipo_remapping=self.SIPO_REMAPPING)
        BaseBVGPanel.__init__(self,
                              artnet,
                              name,
                              universe=universe,
                              piso_remapping=self.PISO_REMAPPING,
                              sipo_remapping=self.SIPO_REMAPPING)
        self.address = self.calculate_address()

    def calculate_address(self) -> int:
        return 15 - sum(2**i * self._input_states[pin] for i, pin in enumerate(self.ADDRESS_PINS))

    def update(self):
        super()._update_states()
        self.address = self.calculate_address()
    
    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            old_bits = self._input_states[::]
            old_address = self.address
            self.update()

            button_changed = False
            for i in range(self._number_of_bits):
                if self._piso_remapping is None:
                    button_id = i
                else:
                    button_id = self._piso_remapping[i]
                    if button_id is None:  # unmapped button, ignore
                        continue
                if old_bits[i] != self._input_states[i]:
                    button_changed = True
                    self.send_button_data(button_id, not self._input_states[i])
            if button_changed:
                self.send_trigger_data(bytes(self._input_states))

            if old_address != self.address:
                self.send_address_data(self.address)

            await asyncio.sleep_ms(sleep_time_ms)
