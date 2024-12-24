import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const


from controlpanel.upy.phys.button import Button
from controlpanel.upy.phys.led_strip import LEDStrip
from controlpanel.upy.phys.pwm import PWM


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
    
    asyncio.create_task(battery_socket_led_strip.run(updates_per_second=10))
    asyncio.create_task(button_battery.run(updates_per_second=10))
    asyncio.create_task(authorization_key.run(updates_per_second=10))
    asyncio.create_task(switch_pos1.run(updates_per_second=10))
    asyncio.create_task(switch_pos2.run(updates_per_second=10))
    # asyncio.create_task(battery_pwm.run(updates_per_second=15))
    # for voltmeter in voltmeters:
    #     asyncio.create_task(voltmeter.run(updates_per_second=10))
        
    print("MAIN LOOP!")
    
    while True:
        # print(battery_pwm.intensity)
        await asyncio.sleep_ms(1000)


BATTERY_LED_STRIP_PIN = const(13)
BATTERY_PWM_PIN = const(19)
AUTHORIZATION_KEY_PIN = const(15)
BATTERY_BUTTON_PIN = const(21)
SWITCH_POS1_PIN = const(5)
SWITCH_POS2_PIN = const(18)
VOLTMETER_PINS = (2, 4, 16, 17)


artnet = ArtNet("255.255.255.255")

battery_socket_led_strip = LEDStrip(artnet, "BatterySlotLadestation-LEDStrip", BATTERY_LED_STRIP_PIN, 30)
authorization_key = Button(artnet, "AuthorizationKeyCharge", AUTHORIZATION_KEY_PIN)
button_battery = Button(artnet, "BatteryButtonLadestation", BATTERY_BUTTON_PIN, invert=True)
switch_pos1 = Button(artnet, "SwitchPos1", SWITCH_POS1_PIN)
switch_pos2 = Button(artnet, "SwitchPos2", SWITCH_POS2_PIN)
battery_pwm = PWM(artnet, "Batterie", BATTERY_PWM_PIN, 1.0)
voltmeters = [PWM(artnet, f"Voltmeter{i+1}", pin) for i, pin in enumerate(VOLTMETER_PINS)]


universe_dict = {
    voltmeters[0].universe: voltmeters[0],
    voltmeters[1].universe: voltmeters[1],
    voltmeters[2].universe: voltmeters[2],
    voltmeters[3].universe: voltmeters[3],
    battery_socket_led_strip.universe: battery_socket_led_strip,
    }


artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
