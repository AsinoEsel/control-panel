import neopixel
from machine import Pin
from controlpanel.shared.base.led_strip import BaseLEDStrip
from .fixture import Fixture
from controlpanel.shared.compatibility import ArtNet


class LEDStrip(BaseLEDStrip, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 name: str,
                 pin: int,
                 length: int,
                 *,
                 universe: int | None = None
                 ) -> None:
        Fixture.__init__(self, _artnet, name, universe=universe)
        self._neopixels: neopixel.NeoPixel = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)

    def __len__(self):
        return len(self._neopixels)

    def parse_dmx_data(self, data: bytes):
        assert len(data) % 3 == 0, "length of data must be divisible by 3"
        self._neopixels.buf = bytearray(data)
        self._neopixels.write()
