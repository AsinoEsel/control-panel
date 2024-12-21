import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const
from machine import Pin, SoftSPI, freq

from controlpanel.upy.phys.shift_register import PisoShiftRegister
from controlpanel.upy.phys.led_strip import LEDStrip

freq(240000000)


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
    ups = 30
    asyncio.create_task(keyboard_piso_module.run(updates_per_second=ups))
    asyncio.create_task(keyboard_led_strip.run(updates_per_second=ups))

    while True:
        await asyncio.sleep_ms(1000)

artnet = ArtNet()

NUM_KEYBOARD_MODULES = const(15)
NUM_SHIFT_REGISTERS = const(NUM_KEYBOARD_MODULES * 2)

PISO_CLOCK_PIN = const(15)  # 33  # 18
PISO_LATCH_PIN = const(4)  # 4
PISO_SERIALIN_PIN = const(17)  # 15
KEYBOARD_LED_PIN = const(16)

keyboard_piso_module = PisoShiftRegister(artnet, "MainframeKeys", PISO_CLOCK_PIN, PISO_LATCH_PIN, PISO_SERIALIN_PIN, NUM_SHIFT_REGISTERS)
keyboard_led_strip = LEDStrip(artnet, "MainframeLEDs", KEYBOARD_LED_PIN, 16 * NUM_KEYBOARD_MODULES)

universe_dict = {
                 keyboard_led_strip.universe: keyboard_led_strip,
                 }

artnet.subscribe_all(artnet_callback)

asyncio.run(start_main_loop())


print("whoops, end of main.py")
