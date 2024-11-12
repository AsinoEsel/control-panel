import asyncio
from artnet import ArtNet, OpCode
from micropython import const
from machine import Pin, SoftSPI

from devices.phys.shift_register import PisoShiftRegister
from devices.phys.led_strip import led_strip
from devices.base.led_strip import animations as led_animations

def anton_board_button_pressed(button_id: int|None, value: bool):
    print(button_id, value)
    if button_id is None:
        print("what")
        return
    keyboard_led_strip.neopixels[button_id] = (128,0,0) if value else (0,0,0)


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    pass
    # if op_code == 0x9900:
    #     print(reply)
    # print(f"New package from {ip}:{port} with opcode {op_code} and reply {reply}")


async def start_main_loop():
    await main_loop()


async def main_loop():
    
    asyncio.create_task(keyboard_piso_module.run(updates_per_second=10))
    asyncio.create_task(keyboard_led_strip.run(updates_per_second=10))

    while True:
        await asyncio.sleep_ms(1000)

artnet = ArtNet()

NUM_KEYBOARD_MODULES = const(15)
NUM_SHIFT_REGISTERS = const(NUM_KEYBOARD_MODULES * 2)

PISO_CLOCK_PIN = const(18)
PISO_LATCH_PIN = const(4)
PISO_SERIALIN_PIN = const(15)
KEYBOARD_LED_PIN = const(16)

keyboard_piso_module = PisoShiftRegister(artnet, "MainframeKeys", PISO_CLOCK_PIN, PISO_LATCH_PIN, PISO_SERIALIN_PIN, NUM_SHIFT_REGISTERS)
keyboard_led_strip = led_strip.LEDStrip(artnet, "MainframeLEDs", KEYBOARD_LED_PIN, 16 * NUM_KEYBOARD_MODULES)
keyboard_led_strip._animation = led_animations.looping_line(len(keyboard_led_strip), .25, (255, 255, 255), (0, 0, 0), 3000)

artnet.subscribe_all(artnet_callback)

asyncio.run(start_main_loop())


print("whoops, end of main.py")
