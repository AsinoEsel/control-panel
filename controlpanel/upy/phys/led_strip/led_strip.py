import neopixel
from machine import Pin
import asyncio
from controlpanel.shared.base.led_strip import BaseLEDStrip, animations


class LEDStrip(BaseLEDStrip):
    ANIMATIONS: list[None | tuple] = [
        None,
        (animations.strobe, 2.0, 0.5, (0, 15, 0), (0, 0, 0)),
        (animations.scrolling_gradient, (255, 0, 64), (64, 0, 255), 1.0),
    ]

    def __init__(self, artnet, name: str, pin: int, length: int, *, universe: int | None = None) -> None:
        super().__init__(artnet, name, universe=universe)
        self.neopixels = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)
        self._animation = None
        self.set_animation(1)

    def __len__(self):
        return len(self.neopixels)

    def set_animation(self, animation_idx: int):
        self._animation_index = animation_idx
        if animation_idx == 0:
            self._animation = None
        else:
            animation, *args = self.ANIMATIONS[animation_idx]
            print(f"Set animation to {animation_idx} with args {args}")
            self._animation = animation(len(self.neopixels), *args)

    def parse_dmx_data(self, data: bytes):
        new_animation_idx = data[self.DMX_INDEX_ANIMATION]
        if new_animation_idx != self._animation_index:
            self.set_animation(new_animation_idx)
        print(new_animation_idx, len(data), len(self.neopixels.buf) + self.DMX_STARTINDEX_PIXELS)
        if new_animation_idx == 0:
            if not len(data) == len(self.neopixels) + 1:
                return
            self.neopixels.buf = self.decompress_rgb(data[1:])
            # for i in range(len(self.neopixels)):
            #     for c in range(3):
            #         self.neopixels.buf[i*3 + c] = data[i + self.DMX_STARTINDEX_PIXELS]
            #
            #     self.neopixels.buf[i] = data[i + self.DMX_STARTINDEX_PIXELS]
            # self.neopixels.buf[:] = data[self.DMX_STARTINDEX_PIXELS:]
            self.neopixels.write()

    def update(self):
        if not self._animation:
            return
        self.neopixels.buf = next(self._animation)
        self.neopixels.write()

    async def run(self, updates_per_second: int):
        sleep_time_ms = int(1000 / updates_per_second)
        while True:
            self.update()
            await asyncio.sleep_ms(sleep_time_ms)
