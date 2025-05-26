from typing import Any
import time
from threading import Thread
from collections import defaultdict
from .instantiate_manifest import get_instantiated_devices
from controlpanel.shared.base import Sensor, Fixture, Device
from controlpanel.event_manager import *
import pygame as pg
from artnet import ArtNet, OpCode


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

    def __init__(self, artnet: ArtNet):
        self.artnet = artnet
        self.artnet.subscribe_all(self.receive)
        self.print_incoming_packets: bool = False
        self.register: dict[Condition:list[Subscriber]] = defaultdict(list)
        self.devices: dict[str: Device] = get_instantiated_devices(artnet)
        self.sensor_dict = {name: device for name, device in self.devices.items() if isinstance(device, Sensor)}
        self.fixture_dict = {device.universe: device for device in self.devices.values() if isinstance(device, Fixture)}

    def _parse_op(self, sender: tuple[str, int], ts: float, op_code: OpCode, reply: dict[str: Any]) -> None:
        match op_code:
            case OpCode.ArtTrigger:
                if self.print_incoming_packets:
                    print(f"Receiving ArtTrigger event from {sender[0]}: {reply}")

                key = reply.get("Key")
                if key != KEY_CONTROL_PANEL_PROTOCOL:
                    return

                subkey_raw = reply.get("SubKey")
                if subkey_raw is None:
                    return
                try:
                    subkey = SubKey(subkey_raw)
                except ValueError:
                    print(f"Invalid sub key {subkey_raw}!")
                    return

                data: bytes = reply.get("Data", b"")
                data_fields = data.split(b"\x00", maxsplit=1)
                if len(data_fields) != 2:
                    return

                sensor_name: str = data_fields[0].decode("ascii")
                sensor_data: bytes = data_fields[1]

                sensor: Sensor | None = self.sensor_dict.get(sensor_name)
                if sensor:
                    event_name, event_value = sensor.parse_trigger_data(sensor_data)
                    self.fire_event(Event(sensor_name, event_name, event_value, sender, ts))
                else:
                    self.fire_event(Event("Trigger", sensor_name, sensor_data, sender, ts))

            case OpCode.ArtDmx:
                if self.print_incoming_packets:
                    universe = reply.get("Universe")
                    fixture: Fixture | None = self.fixture_dict.get(universe)
                    values = [int(byte) for byte in reply.get("Data")]
                    if fixture:
                        print(f"Receiving ArtDMX event from {sender[0]} to fixture {fixture.name}: {values}")
                    else:
                        print(f"Receiving ArtDMX event from {sender[0]} to universe {reply.get("Universe")}: {reply.get("Data")}")

            case OpCode.ArtCommand:
                if self.print_incoming_packets:
                    print(f"Receiving ArtCommand event from {sender[0]}: {reply.get("Command")}")

    def fire_event(self, event: Event):
        print(f"{"Firing event:":<16}{event.source:<20} -> {event.name:<20} -> {str(event.value):<20} from {event.sender}")
        pg.event.post(pg.event.Event(CONTROL_PANEL_EVENT, source=event.source, name=event.name, value=event.value, sender=event.sender))
        for key_func in self.POSSIBLE_EVENT_TYPES:
            source, name, value = key_func(event.source, event.name, event.value)
            listeners: list[Subscriber] = self.register.get(Condition(source, name, value), [])
            for listener in listeners:
                if not listener.allow_parallelism:
                    if listener.thread is not None and listener.thread.is_alive():
                        print("Cannot start thread: old thread is still alive.")
                        return
                print(f"{"Receiving event:":<16}{event.source:<20} -> {event.name:<20} -> {str(event.value):<20} -> {listener.callback.__name__:<20}")
                listener.thread = Thread(target=listener.callback, args=(event,), daemon=True)
                listener.thread.start()
                if listener.fire_once:
                    listeners.remove(listener)

    def receive(self, op_code: OpCode, ip: str, port: int, reply: Any) -> None:
        # if self.print_incoming_packets:
            # print(f"Received {op_code} from {ip}:{port}")
            # for k, v in reply.items():
            #     print(f"\t{k} = {v}")

        sender = (ip, port)
        ts = time.time()

        self._parse_op(sender, ts, op_code, reply)

    def subscribe(self, callback: CallbackType, source: SourceNameType, event_name: EventNameType, condition_value: EventValueType = None, *, fire_once=False, allow_parallelism: bool=False):
        listener = Subscriber(callback, fire_once, allow_parallelism)
        condition = Condition(source, event_name, condition_value)
        self.register[condition].append(listener)
