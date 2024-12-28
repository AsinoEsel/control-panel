import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const
from machine import Pin, SoftSPI, reset

# from controlpanel.upy.phys.rfid_reader import RFIDReader
from controlpanel.upy.phys.led_strip import LEDStrip
from controlpanel.upy.phys.control_panel import BananaPlugs
from controlpanel.upy.phys.pwm import PWM


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    if op_code == OpCode.ArtCommand:
        command = reply.get("Command")
        if command == "RESET":
            reset()
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
    asyncio.create_task(pilz_leds.run(updates_per_second=10))
    asyncio.create_task(banana_plugs.run(updates_per_second=10))

    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)

PILZ_LED_PIN = const(16)

UV_LED = const(21)

artnet = ArtNet("255.255.255.255")

pilz_leds = LEDStrip(artnet, "PilzLEDs", PILZ_LED_PIN, 10)

banana_plugs = BananaPlugs(artnet, "BananaPlugs", [33, 2, 32, 4], [15, 13, 12, 14, 27, 26])
# orange, blau, rot, gelb, schwarz, grün

uv_strobe = PWM(artnet, "UVStrobe", UV_LED, 1.0)

universe_dict = {
                 pilz_leds.universe: pilz_leds,
                 uv_strobe.universe: uv_strobe,
                 }


artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
