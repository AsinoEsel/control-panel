from ...base.sensor import Sensor
try:
    from micropython import const
except ImportError:
    const = lambda x: x


class BaseBananaPlugs(Sensor):
    NO_CONNECTION = const(255)

    def __init__(self, artnet, name: str, plug_count: int):
        super().__init__(artnet, name)
        self.connections: list[int] = [self.NO_CONNECTION for _ in range(plug_count)]
