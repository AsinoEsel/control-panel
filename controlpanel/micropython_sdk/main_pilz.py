import asyncio
from artnet import my_artnet, OpCode
from micropython import const
import _thread
import time
from machine import Pin, SoftSPI

from devices.phys.rfid_reader import RFIDReader
from devices.phys.led_strip import led_strip
from devices.base.led_strip import animations as led_animations
from devices.phys.control_panel import BananaPlugs
from devices.phys.pwm import PWM
from devices.base.pwm import animations as pwm_animations


def banana_plug_callback(plug_id: int, connection: int|None):
    print(f"Plug {plug_id} connected with {connection}")


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    if op_code == OpCode.ArtDmx:
        universe = reply.get("Universe")
        data = reply.get("Data")
        device = universe_dict.get(universe)
        if device is None:
            return
        # print(f"Parsing dmx data {data} for device {device.name}")
        device.parse_dmx_data(data)


async def start_main_loop():
    await main_loop()


async def main_loop():
    
    asyncio.create_task(pilz_rfid_reader.run(updates_per_second=10))
    asyncio.create_task(pilz_leds.run(updates_per_second=10))
    asyncio.create_task(uv_strobe.run(updates_per_second=10))
    asyncio.create_task(banana_plugs.run(updates_per_second=10))

    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


BAUDRATE = const(100000)
RFID_CLOCK_PIN = const(18)  # grau
RFID_MOSI_PIN = const(23)  # lila
RFID_MISO_PIN = const(19)  # blau
RFID_RST_PIN = const(17)  # gelb  # 27
RFID_CS_PIN = const(5)  # SDA weiß  # 26
# 3.3 ORANGE
# GND GRÜN

PILZ_LED_PIN = const(16)

UV_LED = const(21)

spi = SoftSPI(baudrate=BAUDRATE, polarity=1, phase=0, sck=Pin(RFID_CLOCK_PIN), mosi=Pin(RFID_MOSI_PIN), miso=Pin(RFID_MISO_PIN))
pilz_rfid_reader = RFIDReader("PilzRFID", spi, RFID_RST_PIN, RFID_CS_PIN)


pilz_leds = led_strip.LEDStrip("PilzLEDs", PILZ_LED_PIN, 5)
pilz_leds._animation = led_animations.strobe(len(pilz_leds), 1, 0.5, (100, 100, 0), (0, 0, 0))

banana_plugs = BananaPlugs("BananaPlugs", [4, 2, 33, 32], [15, 13, 12, 14, 27, 26], callback=banana_plug_callback)
# orange, gelb, rot, blau, schwarz, grün

from math import sin
uv_strobe = PWM("UVStrobe", UV_LED, 1.0, intensity_function=lambda t: abs(sin(t/1000)))

universe_dict = {
                 pilz_leds.universe: pilz_leds,
                 uv_strobe.universe: uv_strobe,
                 }


my_artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
