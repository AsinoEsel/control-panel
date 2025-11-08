from controlpanel.shared.compatibility import const


class BaseBananaPlugs:
    DEFAULT_POLLING_RATE_HZ = const(1.0)
    NO_CONNECTION = const(255)

    def __init__(self, plug_count: int):
        self._connections: list[int] = [self.NO_CONNECTION for _ in range(plug_count)]
