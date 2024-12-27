import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const
from machine import reset

from controlpanel.upy.phys.control_panel.bvg_panel import BVGPanel
from controlpanel.upy.phys.button import Button
from controlpanel.upy.phys.led_strip import led_strip
from controlpanel.upy.phys.shift_register import PisoShiftRegister, SipoShiftRegister


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
        print(f"Parsing dmx data {data} for device {device.name}")
        device.parse_dmx_data(data)


async def start_main_loop():
    await main_loop()


async def main_loop():

    asyncio.create_task(bvg_panel.run(updates_per_second=10))
    asyncio.create_task(authorization_key.run(updates_per_second=10))
    asyncio.create_task(button_battery.run(10))
    asyncio.create_task(battery_led_strip.run(10))

    print("MAIN LOOP!")
    tick = 0
    while True:
        # tick += 1
        # print("tick")
        # bvg_panel._output_states = [1 if tick % 2 == 0 else 0 for _ in range(bvg_panel._number_of_bits)]
        await asyncio.sleep_ms(60000//120)


LATCH_PIN = const(21)
CLOCK_PIN = const(19)
SERIAL_OUT_PIN = const(4)
SERIAL_IN_PIN = const(13)

LED_PIN = const(22)

BATTERY_BUTTON = const(14)

KEY_PIN = const(12)

if __name__ == "__main__":

    artnet = ArtNet(ip="255.255.255.255")

    # bvg_panel = BVGPanel(artnet, "TestBVGPanel", CLOCK_PIN, LATCH_PIN, SERIAL_IN_PIN, SERIAL_OUT_PIN)
    # bvg_panel = PisoSipoModule(artnet, "BVGPanel", CLOCK_PIN, LATCH_PIN, SERIAL_IN_PIN, SERIAL_OUT_PIN, count=10)
    # bvg_panel = PisoShiftRegister(artnet, "BVGPanel", CLOCK_PIN, LATCH_PIN, SERIAL_IN_PIN, count=10)
    bvg_panel = SipoShiftRegister(artnet, "BVGPanel", CLOCK_PIN, LATCH_PIN, SERIAL_OUT_PIN, count=8)
    battery_led_strip = led_strip.LEDStrip(artnet, "BatterySlotBVG-LEDStrip", LED_PIN, 30)
    # battery_led_strip._animation = animations.strobe(len(battery_led_strip), 1, 0.5, (100, 0, 0), (0, 0, 0))
    button_battery = Button(artnet, "BatteryButton", BATTERY_BUTTON)
    authorization_key = Button(artnet, "AuthorizationKeyBVG", KEY_PIN)

    universe_dict = {
                     bvg_panel.universe: bvg_panel,
                     battery_led_strip.universe: battery_led_strip
                     }

    artnet.subscribe_all(artnet_callback)

    asyncio.run(start_main_loop())
