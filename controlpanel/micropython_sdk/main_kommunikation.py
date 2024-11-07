import asyncio
from artnet import ArtNet, OpCode
from micropython import const
from machine import Pin, SoftSPI
from devices.phys.button import Button


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
    
    for button in rgb_buttons:
        asyncio.create_task(button.run(updates_per_second=10))
    asyncio.create_task(power_button.run(updates_per_second=10))
    
    while True:
        # keeping the loop alive
        await asyncio.sleep_ms(1000)


if __name__ == "__main__":
    artnet = ArtNet(ip="255.255.255.255")

    rgb_buttons = [Button(artnet, "ButtonRed", 14, invert=True),
                   Button(artnet, "ButtonGreen", 13),
                   Button(artnet, "ButtonBlue", 12)]
    power_button = Button(artnet, "ButtonPower", 4)

    universe_dict = {
        }

    artnet.subscribe_all(artnet_callback)

    asyncio.run(start_main_loop())
