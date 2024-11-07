import asyncio
from artnet import my_artnet, OpCode
from micropython import const
from machine import Pin, SoftSPI

from control_panel import BananaPlugs


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    pass
    # print(f"New package from {ip}:{port} with opcode {op_code} and reply {reply}")


def banana_plug_callback(plug_id: int, connection: int|None):
    print(f"Plug {plug_id} connected with {connection}")


async def start_main_loop():
    await main_loop()


async def main_loop():
    
    asyncio.create_task(banana_plugs.run(updates_per_second=10))
    
    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


banana_plugs = BananaPlugs([4,2,33,32], [15,13,12,14,27,26], banana_plug_callback)


my_artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
