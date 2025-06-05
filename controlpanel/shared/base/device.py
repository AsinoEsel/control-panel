try:
    from artnet import ArtNet
except ImportError:
    from controlpanel.upy.artnet import ArtNet


class Device:

    def __init__(self, _artnet: ArtNet, name: str):
        self._artnet: ArtNet = _artnet
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name
