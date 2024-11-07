from .base_piso_shift_register import BasePisoShiftRegister
from .base_sipo_shift_register import BaseSipoShiftRegister


class BasePisoSipoModule(BasePisoShiftRegister, BaseSipoShiftRegister):
    def __init__(self,
                 artnet,
                 name: str,
                 count=1,
                 *,
                 callback=None,
                 universe: int | None = None,
                 piso_remapping: list[int] | None = None,
                 sipo_remapping: list[int] | None = None):
        BasePisoShiftRegister.__init__(self, artnet, name, count, callback=callback, remapping=piso_remapping)
        BaseSipoShiftRegister.__init__(self, artnet, name, count, universe=universe, remapping=sipo_remapping)
        self._piso_remapping = piso_remapping
        self._sipo_remapping = sipo_remapping
