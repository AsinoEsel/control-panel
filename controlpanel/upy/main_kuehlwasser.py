import asyncio
from artnet import my_artnet, OpCode
from micropython import const
import _thread
import time
from machine import Pin, SoftSPI


from devices.phys.led_strip import LEDStrip
from devices.base.led_strip import animations as led_animations
from devices.phys.voltmeter import Voltmeter
from devices.phys.water_flow_sensor import WaterFlowSensor
from devices.phys.pwm import PWM

WATER_FLOW_SENSOR_PIN = const(4)
VOLTMETER_PRESSURE_PIN = const(12)
VOLTMETER_TEMPERATURE_PIN = const(13)
LED_STRIPE_PIN = const(14)
WARNING_LED_PIN = const(2)


total_collected_water = 0

def water_flow_callback(water_flow):
    global total_collected_water
    total_collected_water += water_flow
    print(f"Collected water: {water_flow}")
    print(f"Total collected water: {total_collected_water}")


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
    
    asyncio.create_task(water_flow_sensor.run(updates_per_second=0.1))
    asyncio.create_task(voltmeter_pressure.run(updates_per_second=5))
    asyncio.create_task(voltmeter_temperature.run(updates_per_second=5))
    asyncio.create_task(warning_led.run(updates_per_second=10))
    asyncio.create_task(led_strip.run(updates_per_second=10))

    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


from math import sin

water_flow_sensor = WaterFlowSensor("WaterFlowSensor", WATER_FLOW_SENSOR_PIN)
voltmeter_pressure = PWM("WaterPressure", VOLTMETER_PRESSURE_PIN, 1.0, intensity_function=lambda t: abs(sin(t/5000)))
voltmeter_temperature = PWM("Temperature", VOLTMETER_TEMPERATURE_PIN, 1.0, intensity_function=lambda t: abs(sin(t/5000)))
# voltmeter_pressure = Voltmeter("WaterPressure", VOLTMETER_PRESSURE_PIN, intensity_function=lambda t: abs(sin(t/5000)))
# voltmeter_temperature = Voltmeter("Temperature", VOLTMETER_TEMPERATURE_PIN, intensity_function=lambda t: abs(sin(t/10000)))
led_strip = LEDStrip("StatusLEDs", LED_STRIPE_PIN, 3)  # Betriebpumpe 1, Betriebpumpe 2, Sammelstörung7
led_strip._animation = led_animations.strobe(3, .5, 0.5, color1=(50,50,50))
warning_led = PWM("WarnLED", WARNING_LED_PIN, 1.0, intensity_function=lambda t: (1.0 if t%2==0 else 0.0))


my_artnet.subscribe_all(artnet_callback)


universe_dict = {
    warning_led.universe: warning_led,
    led_strip.universe: led_strip,
    voltmeter_pressure.universe: voltmeter_pressure,
    voltmeter_temperature.universe: voltmeter_temperature,
    }


asyncio.run(start_main_loop())


print("whoops, end of main.py")
