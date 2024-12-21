import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const
import time

from controlpanel.upy.phys.pwm import PWM
from controlpanel.upy.phys.button import Button
from controlpanel.upy.phys.led_strip import led_strip
# from controlpanel.upy.phys.led_strip import animations as led_animations


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    if op_code == OpCode.ArtDmx:
        print(f"Received DMX at universe {reply.get("Universe")}...")
        universe = reply.get("Universe")
        data = reply.get("Data")
        device = universe_dict.get(universe)
        if device is None:
            return
        print(f"Parsing dmx data {data} for device {device.name}")
        device.parse_dmx_data(data)


async def start_main_loop():
    await main_loop()


async def main_loop():
    
    asyncio.create_task(big_red_button.run(updates_per_second=10))
    # asyncio.create_task(chronometer.run(updates_per_second=10))
    asyncio.create_task(status_led_strip.run(updates_per_second=2))
    
    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


artnet = ArtNet(ip="255.255.255.255")

CHRONOMETER_PWM_PIN = const(4)
BIG_RED_BUTTON_PIN = const(14)
LED_STRIP_PIN = const(5)

chronometer = PWM(artnet, "Chronometer", CHRONOMETER_PWM_PIN, intensity=0.6)
big_red_button = Button(artnet, "BigRedButton", BIG_RED_BUTTON_PIN)
status_led_strip = led_strip.LEDStrip(artnet, "ChronometerLampen", LED_STRIP_PIN, 3)
# status_led_strip._animation = led_animations.strobe(len-(status_led_strip), 1, 0.5, (0, 0, 0), (100, 100, 0))


universe_dict = {
                 status_led_strip.universe: status_led_strip,
                 chronometer.universe: chronometer,
                 }


artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
