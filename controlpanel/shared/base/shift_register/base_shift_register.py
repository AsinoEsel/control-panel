try:
    from micropython import const
except ImportError:
    def const(x): return x


class BaseShiftRegister:
    BITS_PER_REGISTER = const(8)

    def __init__(self, count: int, *, remapping: list[int] | None = None):
        self._number_of_bits = count * self.BITS_PER_REGISTER
        assert remapping is None or len(remapping) == self._number_of_bits, \
            "Remapping list needs to be same length as number of states"
        self._remapping = remapping
