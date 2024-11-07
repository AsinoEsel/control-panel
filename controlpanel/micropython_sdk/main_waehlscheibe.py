import asyncio
from artnet import my_artnet, OpCode
from micropython import const

from machine import Pin, SoftSPI

from devices.phys.button import Button
from devices.phys.rotary_dial import RotaryDial
from devices.phys.shift_register import SipoShiftRegister
from devices.phys.seven_segment import SevenSegmentDisplay
from devices.phys.rfid_reader import RFIDReader


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
    
    asyncio.create_task(rotary_dial.run(updates_per_second=5))
    asyncio.create_task(power_switch.run(updates_per_second=10))
    asyncio.create_task(sipo_register.run(updates_per_second=5))
    asyncio.create_task(seven_segment2.run(updates_per_second=2))
    asyncio.create_task(seven_segment1.run(updates_per_second=2))
    asyncio.create_task(rfid_reader.run(updates_per_second=50))

    
    tick=0
    while True:
        import time
        tick+=1
        sipo_register._output_states = [1 if tick%2==0 else 0 for _ in range(sipo_register._number_of_bits)]
        seven_segment1.text = str(tick)
        seven_segment2.text = str(tick*2)
        # keeping the loop alive
        await asyncio.sleep_ms(1000)

    
DIAL_COUNTER_PIN = const(12)
DIAL_RESET_PIN = const(13)

SIPO_LATCH_PIN = const(21)
SIPO_SERIALOUT_PIN = const(4)
SIPO_CLOCK_PIN = const(22)

POWER_SWITCH_PIN = const(32)

BAUDRATE = const(100000)
DISPLAY_CLK_PIN = const(18)
DISPLAY_MOSI_PIN = const(23)  # DIN
DISPLAY1_CS_PIN = const(19)  # LODA1
DISPLAY2_CS_PIN = const(2)  # LODA2

RFID_CS_PIN = const(5)  # SDA
RFID_MISO_PIN = const(14)
RFID_RST_PIN = const(27)


spi = SoftSPI(baudrate=BAUDRATE, polarity=1, phase=0, sck=Pin(DISPLAY_CLK_PIN), mosi=Pin(DISPLAY_MOSI_PIN), miso=Pin(RFID_MISO_PIN))
seven_segment1 = SevenSegmentDisplay("Display1", spi, DISPLAY1_CS_PIN)
seven_segment2 = SevenSegmentDisplay("Display2", spi, DISPLAY2_CS_PIN)

rotary_dial = RotaryDial("RotaryDial", DIAL_COUNTER_PIN, DIAL_RESET_PIN)
sipo_register = SipoShiftRegister("RedYellowLEDs", SIPO_CLOCK_PIN, SIPO_LATCH_PIN, SIPO_SERIALOUT_PIN, 1)
power_switch = Button("PowerSwitch", POWER_SWITCH_PIN)

rfid_reader = RFIDReader("RFIDLogin", spi, RFID_RST_PIN, RFID_CS_PIN)


universe_dict = {
    seven_segment1.universe: seven_segment1,
    seven_segment2.universe: seven_segment2,
    sipo_register.universe: sipo_register,
    }


my_artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
