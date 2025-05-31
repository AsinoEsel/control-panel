from .sensor import Sensor
try:
    from artnet import ArtNet
except ImportError:
    from controlpanel.upy.artnet import ArtNet


class BaseButton(Sensor):
    def __init__(self, artnet: ArtNet, name: str) -> None:
        super().__init__(artnet, name)
