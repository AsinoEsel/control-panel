import asyncio
from artnet import ArtNet, OpCode
from micropython import const

from machine import Pin

from devices.phys.button import Button
from devices.phys.rotary_dial import RotaryDial
from devices.phys.shift_register import SipoShiftRegister
from devices.phys.seven_segment import SevenSegmentDisplay
# from devices.phys.rfid_reader import RFIDReader


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

    tick = 0
    while True:
        import time
        tick += 1
        sipo_register._output_states = [1 if tick % 2 == 0 else 0 for _ in range(sipo_register._number_of_bits)]
        seven_segment.text("CUR TICK" + str(tick))
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


if __name__ == "__main__":

    artnet = ArtNet(ip="255.255.255.255")

    DIAL_COUNTER_PIN = const(12)
    DIAL_RESET_PIN = const(23)  # formerly 13

    SIPO_LATCH_PIN = const(21)
    SIPO_SERIALOUT_PIN = const(4)
    SIPO_CLOCK_PIN = const(22)

    POWER_SWITCH_PIN = const(32)

    # BAUDRATE = const(100000)
    DISPLAY_CS_PIN = const(19)  # LODA

    # RFID_CS_PIN = const(5)  # SDA
    # RFID_MISO_PIN = const(14)
    # RFID_RST_PIN = const(27)

    seven_segment = SevenSegmentDisplay(artnet, "SevenSegmentDisplay", digits=16, gpio_chip_select=DISPLAY_CS_PIN)
    rotary_dial = RotaryDial(artnet, "RotaryDial", DIAL_COUNTER_PIN, DIAL_RESET_PIN)
    sipo_register = SipoShiftRegister(artnet, "RedYellowLEDs", SIPO_CLOCK_PIN, SIPO_LATCH_PIN, SIPO_SERIALOUT_PIN, 1)
    power_switch = Button(artnet, "PowerSwitch", POWER_SWITCH_PIN)
    # rfid_reader = RFIDReader("RFIDLogin", spi, RFID_RST_PIN, RFID_CS_PIN)

    universe_dict = {
        # seven_segment.universe: seven_segment,
        sipo_register.universe: sipo_register,
        }

    artnet.subscribe_all(artnet_callback)

    asyncio.run(start_main_loop())

    print("whoops, end of main.py")
