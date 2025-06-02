from typing import Any
import time
from threading import Thread
from collections import defaultdict
import artnet
from controlpanel.shared.base import Sensor, Fixture, Device
from controlpanel.event_manager.dummy import SensorMixin
from controlpanel.event_manager import *
import pygame as pg
from artnet import ArtNet, OpCode
import importlib.resources
import json
import io
from . import dummy, EventSourceType, EventActionType, EventValueType


class EventManager:
    POSSIBLE_EVENT_TYPES = [
        lambda source, name, value: (source, name, value),
        lambda source, name, value: (source, name, None),
        lambda source, name, value: (source, None, value),
        lambda source, name, value: (source, None, None),
        lambda source, name, value: (None, name, value),
        lambda source, name, value: (None, name, None),
        lambda source, name, value: (None, None, value),
        lambda source, name, value: (None, None, None),
    ]
    DEVICE_MANIFEST_FILENAME = 'device_manifest.json'

    def __init__(self, artnet: ArtNet):
        self.artnet = artnet
        self.artnet.subscribe_all(self.receive)
        self.print_incoming_arttrigger_packets: bool = False
        self.print_incoming_artdmx_packets: bool = False
        self.print_incoming_artcmd_packets: bool = False
        self.register: dict[Condition:list[Subscriber]] = defaultdict(list)
        self.devices: dict[str: Device] = self._get_devices()
        self.sensor_dict = {name: device for name, device in self.devices.items() if isinstance(device, Sensor)}
        self.fixture_dict = {device.universe: device for device in self.devices.values() if isinstance(device, Fixture)}
        self.ip = self._get_local_ip()

    @staticmethod
    def _get_local_ip() -> str:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'
        finally:
            s.close()

    def _get_devices(self, *, assign_sequential_universes: bool = False, start_universe: int = 5000) -> dict[str: Device]:
        """Read the device_manifest.json and instantiate the devices into a dictionary.
        NOTE: assign_sequential_universes is not yet implemented in the upy package, rendering the feature effectively broken.
        """
        with importlib.resources.open_binary("controlpanel.shared", self.DEVICE_MANIFEST_FILENAME) as file:
            manifest = json.load(io.BytesIO(file.read()))

        devices = dict()
        universe = start_universe
        for esp_name, devices_data in manifest.items():
            for (cls_name, kwargs) in devices_data:
                cls = getattr(dummy, cls_name)
                if cls is None:
                    print(cls_name)
                if issubclass(cls, Fixture):
                    if assign_sequential_universes and kwargs.get("universe") is None:
                        kwargs["universe"] = universe
                        print(f"Assigned universe {universe} to {kwargs.get("name", "<UNKNOWN>")}.")
                        universe += 1
                filtered_params = {key: value for key, value in kwargs.items() if
                                   key in cls.__init__.__code__.co_varnames}
                device = cls(artnet=self.artnet, **filtered_params)
                devices[device.name] = device
        return devices

    def _parse_op(self, sender: tuple[str, int], ts: float, op_code: OpCode, reply: dict[str: Any]) -> None:
        match op_code:
            case OpCode.ArtTrigger:
                if self.print_incoming_arttrigger_packets:
                    print(f"Receiving ArtTrigger event from {sender[0]}: {reply}")

                key = reply.get("Key")
                if key != KEY_CONTROL_PANEL_PROTOCOL:
                    return

                data: bytes = reply.get("Data", b"")
                data_fields = data.split(b"\x00", maxsplit=1)
                if len(data_fields) != 2:
                    return

                sensor_name: str = data_fields[0].decode("ascii")
                sensor_data: bytes = data_fields[1]

                sensor: SensorMixin | None = self.sensor_dict.get(sensor_name)
                if sensor:
                    event_action, event_value = sensor.parse_trigger_payload(sensor_data)
                    self.fire_event(sensor_name, event_action, event_value, sender=sender, ts=ts)
                else:
                    self.fire_event("Trigger", sensor_name, sensor_data, sender=sender, ts=ts)

            case OpCode.ArtDmx:
                if self.print_incoming_artdmx_packets:
                    universe = reply.get("Universe")
                    fixture: Fixture | None = self.fixture_dict.get(universe)
                    values = [int(byte) for byte in reply.get("Data")]
                    if fixture:
                        print(f"Receiving ArtDMX event from {sender[0]} to fixture {fixture.name}: {values}")
                    else:
                        print(f"Receiving ArtDMX event from {sender[0]} to universe {reply.get("Universe")}: {reply.get("Data")}")

            case OpCode.ArtCommand:
                if self.print_incoming_artcmd_packets:
                    print(f"Receiving ArtCommand event from {sender[0]}: {reply.get("Command")}")

    def fire_event(self,
                   source: EventSourceType,
                   action: EventActionType,
                   value: EventValueType, *,
                   sender: tuple[str, int] | None = None,
                   ts: float | None = None) -> None:
        sender = sender if sender is not None else (self.ip, artnet.ART_NET_PORT)
        ts = ts if ts is not None else time.time()
        event = Event(source, action, value, sender, ts)
        print(f"{"Firing event:":<16}{event.source:<20} -> {event.action:<20} -> {str(event.value):<20} from {event.sender}")
        pg.event.post(pg.event.Event(CONTROL_PANEL_EVENT, source=event.source, name=event.action, value=event.value, sender=event.sender))
        for key_func in self.POSSIBLE_EVENT_TYPES:
            source, name, value = key_func(event.source, event.action, event.value)
            listeners: list[Subscriber] = self.register.get(Condition(source, name, value), [])
            for listener in listeners:
                if not listener.allow_parallelism:
                    if listener.thread is not None and listener.thread.is_alive():
                        print("Cannot start thread: old thread is still alive.")
                        return
                print(f"{"Receiving event:":<16}{event.source:<20} -> {event.action:<20} -> {str(event.value):<20} -> {listener.callback.__name__:<20}")
                listener.thread = Thread(target=listener.callback, args=(event,), daemon=True)
                listener.thread.start()
                if listener.fire_once:
                    listeners.remove(listener)

    def receive(self, op_code: OpCode, ip: str, port: int, reply: Any) -> None:
        sender = (ip, port)
        ts = time.time()
        self._parse_op(sender, ts, op_code, reply)

    def subscribe(self, callback: CallbackType, source: EventSourceType, action: EventActionType, value: EventValueType = None, *, fire_once=False, allow_parallelism: bool=False):
        listener = Subscriber(callback, fire_once, allow_parallelism)
        condition = Condition(source, action, value)
        self.register[condition].append(listener)
