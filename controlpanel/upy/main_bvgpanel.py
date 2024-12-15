import asyncio
from artnet import ArtNet, OpCode
from micropython import const

from devices.phys.control_panel.bvg_panel import BVGPanel
from devices.phys.button import Button
from devices.phys.led_strip import led_strip
from devices.base.led_strip import animations


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
    
    asyncio.create_task(bvg_panel.run(updates_per_second=10))
    asyncio.create_task(authorization_key.run(updates_per_second=10))
    asyncio.create_task(button_battery.run(10))
    asyncio.create_task(battery_led_strip.run(10))

    print("MAIN LOOP!")

    while True:
        await asyncio.sleep_ms(60000//120)


LATCH_PIN = const(21)
CLOCK_PIN = const(19)
SERIAL_OUT_PIN = const(4)
SERIAL_IN_PIN = const(14)

LED_PIN = const(32)

BATTERY_BUTTON = const(13)

KEY_PIN = const(12)

if __name__ == "__main__":

    artnet = ArtNet(ip="255.255.255.255")

    bvg_panel = BVGPanel(artnet, "TestBVGPanel", CLOCK_PIN, LATCH_PIN, SERIAL_IN_PIN, SERIAL_OUT_PIN)
    battery_led_strip = led_strip.LEDStrip(artnet, "BatterySlotBVG-LEDStrip", LED_PIN, 30)
    battery_led_strip._animation = animations.strobe(len(battery_led_strip), 1, 0.5, (100, 0, 0), (0, 0, 0))
    button_battery = Button(artnet, "BatteryButton", BATTERY_BUTTON)
    authorization_key = Button(artnet, "AuthorizationKeyBVG", KEY_PIN)

    universe_dict = {
                     bvg_panel.universe: bvg_panel,
                     battery_led_strip.universe: battery_led_strip
                     }

    artnet.subscribe_all(artnet_callback)

    asyncio.run(start_main_loop())
