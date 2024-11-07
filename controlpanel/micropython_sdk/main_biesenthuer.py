import asyncio
from artnet import my_artnet, OpCode
from micropython import const

from devices.phys.led_strip import led_strip
from devices.base.led_strip import animations as led_animations


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    if op_code == OpCode.ArtDmx:
        pass


async def start_main_loop():
    await main_loop()


async def main_loop():
    
    asyncio.create_task(biesenthuer_leds.run(2))

    print("MAIN LOOP!")

    from random import randrange, choice
    colors = [(255, 0, 0), (255, 255, 0), (255, 255, 255), (0, 0, 255)]
    while True:
        for i in range(len(biesenthuer_leds)):
            if not randrange(2):
                biesenthuer_leds[i] = (0, 0, 0)
            else:
                biesenthuer_leds[i] = (255, 0, 0)
        biesenthuer_leds.update()
        await asyncio.sleep_ms(const(60000//120))


LED_PIN = const(16)


biesenthuer_leds = led_strip.LEDStrip("Biesenthuer-LEDStrip", LED_PIN, 30)
# biesenthuer_leds._animation = led_animations.strobe(len(biesenthuer_leds), 1, 0.5, (100, 0, 0), (0, 0, 0))


my_artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
