from typing import Any
from types import ModuleType
import time
from threading import Thread
from collections import defaultdict
from controlpanel.shared.base import Device
from controlpanel.api.dummy import Sensor, Fixture
from controlpanel.api import Condition, Subscriber, KEY_CONTROL_PANEL_PROTOCOL, Event, CallbackType, CONTROL_PANEL_EVENT
import pygame as pg
from artnet import ArtNet, OpCode, ART_NET_PORT
import importlib.resources
import json
import io
from .commons import EventSourceType, EventActionType, EventValueType


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
        self._artnet = artnet
        self._artnet.subscribe_all(self._receive)
        self._callback_register: dict[Condition, list[Subscriber]] = defaultdict(list)
        self.devices: dict[str, Device] = dict()
        self._sensor_dict: dict[str, Sensor] = dict()
        self._fixture_dict: dict[str, Fixture] = dict()
        self.ip = self._get_local_ip()

        self.print_incoming_arttrigger_packets: bool = False
        self.print_incoming_artdmx_packets: bool = False
        self.print_incoming_artcmd_packets: bool = False
        self.print_incoming_artpollreply_packets: bool = False

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

    def instantiate_devices(self, libs: list[ModuleType], *, assign_sequential_universes: bool = False, start_universe: int = 5000) -> None:
        """Read the device_manifest.json and instantiate the devices into a dictionary.
        NOTE: assign_sequential_universes is not yet implemented in the upy package, rendering the feature effectively broken.
        """
        def find_class_in_modules(modules: list[ModuleType], name: str) -> type | None:
            for module in modules:
                cls = getattr(module, name, None)
                if cls and isinstance(cls, type):
                    return cls
            return None

        with importlib.resources.open_binary("controlpanel.shared", self.DEVICE_MANIFEST_FILENAME) as file:
            manifest = json.load(io.BytesIO(file.read()))

        universe = start_universe
        for esp_name, devices_data in manifest.items():
            for (cls_name, phys_kwargs, dummy_kwargs) in devices_data:
                kwargs: dict = phys_kwargs | dummy_kwargs
                cls = find_class_in_modules(libs, cls_name)
                if cls is None:
                    print(f"Failed to find {cls_name} in any of these modules: {[lib.__name__ for lib in libs]}")
                    continue
                if issubclass(cls, Fixture) and assign_sequential_universes and kwargs.get("universe") is None:
                    kwargs["universe"] = universe
                    print(f"Assigned universe {universe} to {kwargs.get("name", "<UNKNOWN>")}.")
                    universe += 1
                filtered_kwargs = {key: value for key, value in kwargs.items()
                                   if key in cls.__init__.__code__.co_varnames}
                try:
                    device = cls(_artnet=self._artnet, **filtered_kwargs)
                except TypeError:
                    print(f"Type Error raised when instantiating {filtered_kwargs.get("name")}.")
                    raise
                self.devices[device.name] = device

        self._sensor_dict = {name: device for name, device in self.devices.items() if isinstance(device, Sensor)}
        self._fixture_dict = {device.universe: device for device in self.devices.values() if isinstance(device, Fixture)}

    def _parse_op(self, sender: tuple[str, int], ts: float, op_code: OpCode, reply: dict[str, Any]) -> None:
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

                sensor: Sensor | None = self._sensor_dict.get(sensor_name)
                if sensor:
                    event_action, event_value = sensor.parse_trigger_payload(sensor_data)
                    self.fire_event(sensor_name, event_action, event_value, sender=sender, ts=ts)
                else:
                    self.fire_event(sensor_name, "UnknownAction", sensor_data, sender=sender, ts=ts)

            case OpCode.ArtDmx:
                if self.print_incoming_artdmx_packets:
                    universe = reply.get("Universe")
                    fixture: Fixture | None = self._fixture_dict.get(universe)
                    values = [int(byte) for byte in reply.get("Data")]
                    if fixture:
                        print(f"Receiving ArtDMX event from {sender[0]} to fixture {fixture.name}: {values}")
                    else:
                        print(f"Receiving ArtDMX event from {sender[0]} to universe {reply.get("Universe")}: {reply.get("Data")}")

            case OpCode.ArtCommand:
                if self.print_incoming_artcmd_packets:
                    print(f"Receiving ArtCommand event from {sender[0]}: {reply.get("Command")}")

            case OpCode.ArtPollReply:
                if self.print_incoming_artpollreply_packets:
                    print(f"Receiving ArtPollReply event from {sender[0]}: {reply}")

            case _:
                try:
                    print(f"Received an {OpCode(op_code).name} packet from {sender[0]}")
                except ValueError:
                    print(f"Received a packet with invalid op code {hex(op_code)}")


    def fire_event(self,
                   source: EventSourceType,
                   action: EventActionType,
                   value: EventValueType, *,
                   sender: tuple[str, int] | None = None,
                   ts: float | None = None) -> None:
        sender = sender if sender is not None else (self.ip, ART_NET_PORT)
        ts = ts if ts is not None else time.time()
        event = Event(source, action, value, sender, ts)
        print(f"{"Firing event:":<16}{event.source:<20} -> {event.action:<20} -> {str(event.value):<20} from {event.sender}")
        pg.event.post(pg.event.Event(CONTROL_PANEL_EVENT, source=event.source, name=event.action, value=event.value, sender=event.sender))
        for key_func in self.POSSIBLE_EVENT_TYPES:
            source, name, value = key_func(event.source, event.action, event.value)
            listeners: list[Subscriber] = self._callback_register.get(Condition(source, name, value), [])
            for listener in listeners:
                if not listener.allow_parallelism:
                    if listener.thread is not None and listener.thread.is_alive():
                        print("Cannot start thread: old thread is still alive.")
                        return
                print(f"{"Event received: ":<16}{listener.callback.__module__.rsplit(".")[-1]}.{listener.callback.__name__}")
                listener.thread = Thread(target=listener.callback, args=(event,), daemon=True)
                listener.thread.start()
                if listener.fire_once:
                    listeners.remove(listener)

    def _receive(self, op_code: OpCode, ip: str, port: int, reply: Any) -> None:
        sender = (ip, port)
        ts = time.time()
        self._parse_op(sender, ts, op_code, reply)

    def subscribe(self, callback: CallbackType, source: EventSourceType, action: EventActionType, value: EventValueType = None, *, fire_once=False, allow_parallelism: bool=False):
        listener = Subscriber(callback, fire_once, allow_parallelism)
        condition = Condition(source, action, value)
        self._callback_register[condition].append(listener)
