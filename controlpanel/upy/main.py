import utils
from machine import reset
from controlpanel.upy import phys
from controlpanel.upy.artnet import ArtNet, OpCode
from controlpanel.shared.base import Device
from controlpanel.upy.phys import Fixture, Sensor
from controlpanel.shared.compatibility import Callable
import uasyncio as asyncio
import time


class ESP:
    def __init__(self):
        self._name = utils.get_hostname()
        self._artnet = ArtNet()
        self._artnet.subscribe(OpCode.ArtDmx, self.artdmx_callback)
        self._artnet.subscribe(OpCode.ArtCommand, self.artcmd_callback)
        self._artnet.subscribe(OpCode.ArtPoll, self.artpoll_callback)
        self.commands: dict[str, Callable] = {
            "RESET": reset,
            "STOP": self._stop_updating_devices,
        }

        self.devices: dict[str, Device] = self._instantiate_devices()
        self.universes: dict[int, Fixture] = {
            device.universe: device for device in self.devices.values() if isinstance(device, Fixture)
        }
        self.fixtures: dict[str, Fixture] = {
            device.name: device for device in self.devices.values() if isinstance(device, Fixture)
        }
        self.sensors: dict[str, Sensor] = {
            device.name: device for device in self.devices.values() if isinstance(device, Sensor)
        }

        self._update_devices: bool = True

    def _instantiate_devices(self) -> dict[str, Device]:
        manifest = utils.load_json('controlpanel/shared/device_manifest.json')
        if not manifest:
            return dict()
        devices: dict[str, Device] = dict()
        device_list: list = manifest.get(self._name, list())
        for device_data in device_list:
            classname, kwargs, _ = device_data
            cls: type = getattr(phys, classname)
            device: Device = cls(self._artnet, **kwargs)
            devices[device.name] = device
        return devices

    def _stop_updating_devices(self):
        print("Stopping device updates...")
        self._update_devices = False

    async def _update_device(self, device: Sensor | Fixture):
        while self._update_devices:
            await device.update()
            await asyncio.sleep_ms(device.update_rate_ms)

    async def update_all_devices(self):
        tasks = [
            self._update_device(device)
            for device in self.devices.values()
            if device.update_rate_ms > 0
        ]
        await asyncio.gather(*tasks)

    def artcmd_callback(self, op_code: OpCode, ip: str, port: int, reply):
        command = reply.get("Command")
        func = self.commands.get(command)
        if func:
            func()
        else:
            print("Received unknown command: {}".format(command))

    def artdmx_callback(self, op_code: OpCode, ip: str, port: int, reply):
        universe = reply.get("Universe")
        data = reply.get("Data")
        fixture: Fixture = self.universes.get(universe)
        if fixture is None:
            return
        print(f"Parsing dmx data {data} for fixture {fixture.name}")
        fixture.parse_dmx_data(data)

    def artpoll_callback(self, op_code: OpCode, ip: str, port: int, reply):
        print(f"Received ArtPoll packet, sending ArtPollReply @ {time.ticks_ms()}.")
        asyncio.create_task(self.delayed_reply_to_artpoll(ip, port))

    async def delayed_reply_to_artpoll(self, ip: str, port: int):
        from random import randint
        await asyncio.sleep_ms(randint(0, 1000))  # ArtNet 4 standard specifies a random delay of up to 1s
        self._artnet.send_poll_reply(ip=utils.get_local_ip(),
                                     port=self._artnet.port,
                                     address=(ip, port),
                                     short_name=self._name,
                                     long_name="Control Panel ESP32 Node: " + self._name,
                                     mac=utils.get_mac_address(),
                                     )


esp = ESP()
asyncio.run(esp.update_all_devices())
