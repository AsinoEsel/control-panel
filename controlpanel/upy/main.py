import utils
from machine import reset
from controlpanel.upy import phys
from controlpanel.upy.artnet import ArtNet, OpCode
from controlpanel.shared.base import Device
from controlpanel.upy.phys import Fixture, Sensor
import uasyncio as asyncio
try:
    from typing import Callable
except ImportError:
    Callable = object


class ESP:
    def __init__(self):
        self._name = utils.get_hostname()
        self._artnet = ArtNet()
        self._artnet.subscribe(OpCode.ArtDmx, self.artdmx_callback)
        self._artnet.subscribe(OpCode.ArtCommand, self.artcmd_callback)
        self._artnet.subscribe(OpCode.ArtPoll, self.artdmx_callback)
        self.commands: dict[str: Callable[[], None]] = {
            "RESET": reset,
        }

        self.devices: dict[str: Device] = self._instantiate_devices()
        self.universes: dict[int: Fixture] = {
            device.universe: device for device in self.devices.values() if isinstance(device, Fixture)
        }
        self.fixtures: dict[str: Fixture] = {
            device.name: device for device in self.devices.values() if isinstance(device, Fixture)
        }
        self.sensors: dict[str: Sensor] = {
            device.name: device for device in self.devices.values() if isinstance(device, Sensor)
        }


    def _instantiate_devices(self) -> dict[str:Device]:
        manifest = utils.load_json('controlpanel/shared/device_manifest.json')
        if not manifest:
            return dict()
        devices: dict[str: Device] = dict()
        device_list: list = manifest.get(self._name, list())
        for device_data in device_list:
            classname, kwargs, _ = device_data
            cls: type = getattr(phys, classname)
            device: Device = cls(self._artnet, **kwargs)
            devices[device.name] = device
        return devices

    @staticmethod
    async def _poll_sensor(sensor: Sensor):
        while True:
            await sensor.poll()
            await asyncio.sleep_ms(sensor.polling_rate_ms)

    async def poll_all_sensors(self):
        tasks = [asyncio.create_task(self._poll_sensor(sensor)) for sensor in self.sensors.values() if sensor.polling_rate_ms]
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
        ...


esp = ESP()
asyncio.run(esp.poll_all_sensors())
