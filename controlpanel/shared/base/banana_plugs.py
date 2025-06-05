from controlpanel.shared.compatibility import const


class BaseBananaPlugs:
    NO_CONNECTION = const(255)

    def __init__(self, plug_count: int):
        self._connections: list[int] = [self.NO_CONNECTION for _ in range(plug_count)]
