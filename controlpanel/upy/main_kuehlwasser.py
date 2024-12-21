import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const


from controlpanel.upy.phys.led_strip import LEDStrip
# from controlpanel.upy.phys.voltmeter import Voltmeter
from controlpanel.upy.phys.water_flow_sensor import WaterFlowSensor
from controlpanel.upy.phys.pwm import PWM

WATER_FLOW_SENSOR_PIN = const(4)
VOLTMETER_PRESSURE_PIN = const(12)
VOLTMETER_TEMPERATURE_PIN = const(13)
LED_STRIPE_PIN = const(14)
WARNING_LED_PIN = const(2)


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
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
    
    asyncio.create_task(water_flow_sensor.run(updates_per_second=0.1))
    # asyncio.create_task(voltmeter_pressure.run(updates_per_second=5))
    # asyncio.create_task(voltmeter_temperature.run(updates_per_second=5))
    # asyncio.create_task(warning_led.run(updates_per_second=10))
    asyncio.create_task(led_strip.run(updates_per_second=10))

    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


artnet = ArtNet("255.255.255.255")
water_flow_sensor = WaterFlowSensor(artnet, "WaterFlowSensor", WATER_FLOW_SENSOR_PIN)
voltmeter_pressure = PWM(artnet, "WaterPressure", VOLTMETER_PRESSURE_PIN, 1.0)  #intensity_function=lambda t: abs(sin(t/5000))
voltmeter_temperature = PWM(artnet, "Temperature", VOLTMETER_TEMPERATURE_PIN, 1.0)  # intensity_function=lambda t: abs(sin(t/5000))
# voltmeter_pressure = Voltmeter(artnet, "WaterPressure", VOLTMETER_PRESSURE_PIN, intensity_function=lambda t: abs(sin(t/5000)))
# voltmeter_temperature = Voltmeter(artnet, "Temperature", VOLTMETER_TEMPERATURE_PIN, intensity_function=lambda t: abs(sin(t/10000)))
led_strip = LEDStrip(artnet, "StatusLEDs", LED_STRIPE_PIN, 3)  # Betriebpumpe 1, Betriebpumpe 2, Sammelstörung7
warning_led = PWM(artnet, "WarnLED", WARNING_LED_PIN, 1.0)  # intensity_function=lambda t: (1.0 if t%2==0 else 0.0)


artnet.subscribe(OpCode.ArtDmx, artnet_callback)


universe_dict = {
    warning_led.universe: warning_led,
    led_strip.universe: led_strip,
    voltmeter_pressure.universe: voltmeter_pressure,
    voltmeter_temperature.universe: voltmeter_temperature,
    }


asyncio.run(start_main_loop())


print("whoops, end of main.py")
