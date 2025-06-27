from typing import Any, Iterable
from types import ModuleType
import time
from threading import Thread
import asyncio
import inspect
from collections import defaultdict
from controlpanel.shared.base import Device
from controlpanel.api.dummy import Sensor, Fixture
import pygame as pg
from artnet import ArtNet, OpCode, ART_NET_PORT
import importlib.resources
import json
import io
from controlpanel.api.dummy.esp32 import ESP32
from .commons import (
    Event,
    Condition,
    Subscriber,
    CallbackType,
    EventSourceType,
    EventActionType,
    EventValueType,
    KEY_CONTROL_PANEL_PROTOCOL,
    CONTROL_PANEL_EVENT,
)


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
        self._artnet: ArtNet = artnet
        self._artnet.subscribe_all(self._receive)
        Thread(target=artnet.listen, args=(None,), daemon=True).start()

        self.devices: dict[str, Device] = dict()
        self._sensor_dict: dict[str, Sensor] = dict()
        self._fixture_dict: dict[str, Fixture] = dict()
        self._ip: str = self._get_local_ip()

        self._callback_register: dict[Condition, list[Subscriber]] = defaultdict(list)
        self._event_queue = asyncio.Queue()
        self._reply_queue = asyncio.Queue()
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        Thread(target=self._run_async_loop, args=(), daemon=True).start()

        self._artpoll_response_future: asyncio.Future | None = None
        self._nodes: list[ESP32] = list()

        self.print_incoming_arttrigger_packets: bool = False
        self.print_incoming_artdmx_packets: bool = False
        self.print_incoming_artcmd_packets: bool = False
        self.print_incoming_artpollreply_packets: bool = False

    @property
    def ip(self) -> str:
        return self._ip

    def _run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._dispatch_loop())
        self.loop.create_task(self._poll_loop())
        self.loop.run_forever()

    async def _dispatch_loop(self):
        while True:
            event = await self._event_queue.get()
            await self._notify_subscribers(event)

    async def _poll_and_collect(self, timeout=3.0) -> list[dict[str, Any]]:
        # print("Sending poll...")
        replies: list[dict[str, Any]] = []
        self._artnet.send_poll()
        try:
            while True:
                reply: dict[str, Any] = await asyncio.wait_for(self._reply_queue.get(), timeout=timeout)
                # print(f"Got reply from {reply.get("IpAddress")}")
                replies.append(reply)
        except asyncio.TimeoutError:
            # print("Timed out.")
            pass
        return replies

    def _handle_artpoll_replies(self, replies: list[dict[str, Any]]) -> None:
        collected_mac_addresses: set[str] = set()  # a set of all MAC addresses from nodes that replied to our poll
        for reply in replies:
            name: str = reply['ShortName']
            mac: str = reply['Mac']
            collected_mac_addresses.add(mac)
            if mac not in (esp.mac for esp in self._nodes):
                if name not in (esp.name for esp in self._nodes):
                    print(f"Unknown ESP '{name}' with mac {mac} has been registered")
                    esp = ESP32(name)
                    esp.mac = mac
                    esp.ip = reply["IpAddress"]
                    esp.status = reply['NodeReport']
                    self._nodes.append(esp)
                else:
                    esp = next((esp for esp in self._nodes if esp.name == name))
                    esp.mac = mac
                    esp.ip = reply["IpAddress"]
                    esp.status = reply['NodeReport']
                    esp.subsequent_missed_replies = 0
                    print(f"ESP '{name}' with mac {mac} connected for the first time")
            else:
                esp = next((esp for esp in self._nodes if esp.mac == mac), None)
                if esp.subsequent_missed_replies > 0:
                    print(f"ESP '{esp.name}' has regained the connection!")
                esp.name = name
                esp.ip = reply['IpAddress']
                esp.status = reply['NodeReport']
                esp.subsequent_missed_replies = 0
        for esp in self._nodes:
            if esp.status == "Lost connection!" or esp.status == "Never connected":
                continue
            if esp.mac not in collected_mac_addresses:
                esp.subsequent_missed_replies += 1
                print(f"ESP '{esp.name}' failed to reply! ({esp.subsequent_missed_replies} missed repl{"ies" if esp.subsequent_missed_replies > 1 else "y"})")
                if esp.subsequent_missed_replies >= 3:
                    print(f"ESP '{esp.name}' lost the connection!")
                    esp.status = 'Lost connection!'

    async def _poll_loop(self):
        while True:
            replies = await self._poll_and_collect()
            self._handle_artpoll_replies(replies)
            await asyncio.sleep(10.0)

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

    def instantiate_devices(self, libs: Iterable[ModuleType], *, assign_sequential_universes: bool = False, start_universe: int = 5000) -> None:
        """Read the device_manifest.json and instantiate the devices into a dictionary.
        NOTE: assign_sequential_universes is not yet implemented in the upy package, rendering the feature effectively broken.
        """
        def find_class_in_modules(modules: Iterable[ModuleType], name: str) -> type | None:
            for module in modules:
                cls = getattr(module, name, None)
                if cls and isinstance(cls, type):
                    return cls
            return None

        with importlib.resources.open_binary("controlpanel.shared", self.DEVICE_MANIFEST_FILENAME) as file:
            manifest = json.load(io.BytesIO(file.read()))

        universe = start_universe
        for esp_name, devices_data in manifest.items():
            if not esp_name in (esp.name for esp in self._nodes):
                self._nodes.append(ESP32(esp_name))
            esp = next((esp for esp in self._nodes if esp.name == esp_name), None)
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
                    device = (
                        cls(_artnet=self._artnet, _loop=self.loop, _esp=esp, **filtered_kwargs) if issubclass(cls, Fixture) else
                        cls(_artnet=self._artnet, **filtered_kwargs)
                    )
                except TypeError:
                    print(f"Type Error raised when instantiating {filtered_kwargs.get("name")}.")
                    raise

                esp.devices[device.name] = device

        self.devices = {name: device for esp in self._nodes for name, device in esp.devices.items()}
        self._sensor_dict = {name: device for name, device in self.devices.items() if isinstance(device, Sensor)}
        self._fixture_dict = {device.universe: device for device in self.devices.values() if isinstance(device, Fixture)}

    def _parse_trigger(self, reply: dict[str, Any], sender: tuple[str, int], ts: float):
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
        if sensor is None:
            return

        seq = reply.get("SubKey")
        if sensor.should_ignore_seq(seq):
            return
        sensor._seq = seq

        event_action, event_value = sensor.parse_trigger_payload(sensor_data)
        self.fire_event(sensor_name, event_action, event_value, sender=sender, ts=ts)

    def _parse_dmx(self, reply: dict[str, Any], sender: tuple[str, int], ts: float) -> None:
        if not self.print_incoming_artdmx_packets:
            return
        universe = reply.get("Universe")
        fixture: Fixture | None = self._fixture_dict.get(universe)
        values = [int(byte) for byte in reply.get("Data")]
        if fixture:
            print(f"Receiving ArtDMX event from {sender[0]} to fixture {fixture.name}: {values}")
        else:
            print(f"Receiving ArtDMX event from {sender[0]} to universe {reply.get("Universe")}: {reply.get("Data")}")

    def _parse_artpollreply(self, reply: dict[str, Any], sender: tuple[str, int], ts: float) -> None:
        if self.print_incoming_artpollreply_packets:
            print(f"Receiving ArtPollReply event from {sender[0]}: {reply}")
        self.loop.call_soon_threadsafe(self._reply_queue.put_nowait, reply)

    def _parse_artcmd(self, reply: dict[str, Any], sender: tuple[str, int], ts: float) -> None:
        if self.print_incoming_artcmd_packets:
            print(f"Receiving ArtCommand event from {sender[0]}: {reply.get("Command")}")

    def _parse_op(self, sender: tuple[str, int], ts: float, op_code: OpCode, reply: dict[str, Any]) -> None:
        match op_code:
            case OpCode.ArtTrigger:
                self._parse_trigger(reply, sender, ts)
            case OpCode.ArtDmx:
                self._parse_dmx(reply, sender, ts)
            case OpCode.ArtCommand:
                self._parse_artcmd(reply, sender, ts)
            case OpCode.ArtPollReply:
                self._parse_artpollreply(reply, sender, ts)
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
        sender = sender if sender is not None else (self._ip, ART_NET_PORT)
        ts = ts if ts is not None else time.time()
        event = Event(source, action, value, sender, ts)
        print(f"{"Firing event:":<16}{event.source:<20} -> {event.action:<20} -> {str(event.value):<20} from {event.sender}")
        pg.event.post(pg.event.Event(CONTROL_PANEL_EVENT, source=event.source, name=event.action, value=event.value, sender=event.sender))
        asyncio.run_coroutine_threadsafe(self._event_queue.put(event), self.loop)

    async def _notify_subscribers(self, event: Event) -> None:
        for key_func in self.POSSIBLE_EVENT_TYPES:
            source, name, value = key_func(event.source, event.action, event.value)
            subscribers: list[Subscriber] = self._callback_register.get(Condition(source, name, value), [])
            for subscriber in subscribers:
                if not subscriber.allow_parallelism:
                    if subscriber.task is not None and not subscriber.task.done():
                        print(f"[EventManager] Skipping {subscriber.callback.__name__}: still running.")
                        continue
                print(f"{"Event received: ":<16}{subscriber.callback.__module__.rsplit(".")[-1]}.{subscriber.callback.__name__}")

                if inspect.iscoroutinefunction(subscriber.callback):
                    if subscriber.requires_event_arg:
                        task = asyncio.create_task(subscriber.callback(event))
                    else:
                        task = asyncio.create_task(subscriber.callback())
                    subscriber.task = task
                else:
                    # Run sync function in a thread, wrap it in a future
                    if subscriber.requires_event_arg:
                        task = asyncio.to_thread(subscriber.callback, event)
                    else:
                        task = asyncio.to_thread(subscriber.callback)
                    subscriber.task = asyncio.create_task(task)

                if subscriber.fire_once:
                    subscribers.remove(subscriber)

    def _receive(self, op_code: OpCode, ip: str, port: int, reply: Any) -> None:
        if ip == self._ip:
            return  # ignore packet if it's ours
        sender = (ip, port)
        ts = time.time()
        self._parse_op(sender, ts, op_code, reply)

    def subscribe(self,
                  callback: CallbackType,
                  source: EventSourceType,
                  action: EventActionType,
                  value: EventValueType = None,
                  *,
                  fire_once: bool = False,
                  allow_parallelism: bool = False) -> None:
        subscriber = Subscriber(callback, fire_once, allow_parallelism, callback.__code__.co_argcount == 1)
        condition = Condition(source, action, value)
        self._callback_register[condition].append(subscriber)
