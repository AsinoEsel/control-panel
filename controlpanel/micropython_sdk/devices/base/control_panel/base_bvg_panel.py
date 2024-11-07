from ..shift_register import BasePisoSipoModule
try:
    from micropython import const
except ImportError:
    def const(x): return x


class BaseBVGPanel(BasePisoSipoModule):
    SHIFT_REGISTER_COUNT = const(10)

    def __init__(self,
                 artnet,
                 name: str,
                 *,
                 callback=None,
                 universe: int | None = None,
                 piso_remapping: list[int | None] | None = None,
                 sipo_remapping: list[int | None] | None = None):
        super().__init__(
            artnet,
            name,
            self.SHIFT_REGISTER_COUNT,
            callback=callback,
            universe=universe,
            piso_remapping=piso_remapping,
            sipo_remapping=sipo_remapping,
        )
        self.address = 0

    def send_button_data(self, index: int, value: int):
        self.send_data(name=self.name+str(index),
                       subkey=0,  # TODO: fix hardcode
                       payload=(value * 255).to_bytes(1, "big"))

    def send_address_data(self, address: int):
        self.send_data(name=self.name,
                       subkey=9,  # TODO: fix hardcode
                       payload=address.to_bytes(1, "big"))
