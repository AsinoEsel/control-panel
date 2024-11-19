from artnet import ArtNet, OpCode
from typing import Callable, Any
from dataclasses import dataclass
import time
import struct
from .commons import SubKey, KEY_CONTROL_PANEL_PROTOCOL
from threading import Thread


SourceNameType = str
EventNameType = str
EventValueType = bool | int | str | tuple | bytes | None


@dataclass(frozen=True)
class Event:
    source: SourceNameType
    name: EventNameType
    value: EventValueType
    sender: tuple[str, int] | None
    timestamp: float


@dataclass(frozen=True)
class Condition:
    source: SourceNameType
    event_name: EventNameType
    condition: EventValueType


CallbackType = Callable[[Event], None]


@dataclass
class Subscriber:
    callback: CallbackType
    fire_once: bool = False
    allow_parallelism: bool = False
    thread: Thread | None = None


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
        self.register: dict[Condition:list[Subscriber]] = dict()

    def _parse_op(self, sender: tuple[str, int], ts: float, op_code: OpCode, reply: dict[str: Any]) -> None:
        match op_code:
            case OpCode.ArtTrigger:
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

                data = reply.get("Data", b"")

                try:
                    self._parse_sub_key(sender, subkey, data, ts)
                except struct.error as exc:
                    print(f"Parsing of {subkey.name} failed: {exc}")

            case OpCode.ArtDmx:
                self.fire_event(Event("DMX", reply.get("Universe"), reply.get("Data"), sender, ts))

    def _parse_sub_key(self, sender: tuple[str, int], subkey: SubKey, data: bytes, ts: float) -> None:
        data_fields = data.split(b"\x00", maxsplit=1)

        if len(data_fields) < 2:
            return

        event_source = data_fields[0].decode("ascii")
        raw_value = data_fields[1]
        event_name = subkey.name
        parsed_value = self.get_processed_value(raw_value, subkey, data)

        self.fire_event(Event(event_source, event_name, parsed_value, sender, ts))

    @staticmethod
    def get_processed_value(raw_value: bytes, subkey: int, data: bytes) -> EventValueType:

        match subkey:
            case SubKey.PushButton:
                return bool(struct.unpack("B", raw_value)[0])
            case SubKey.RotaryEncoder:
                return struct.unpack("B", raw_value)[0]
            case SubKey.Integer:
                return tuple(
                    struct.unpack("<i", raw_value[i: i + 4])[0]
                    for i in range(0, len(raw_value), 4)
                )
            case SubKey.Double:
                return tuple(
                    struct.unpack("<d", raw_value[i: i + 8])[0]
                    for i in range(0, len(raw_value), 8)
                )
            case SubKey.String:
                return data.split(b"\x00", maxsplit=1)[0].decode("ascii")
            case SubKey.RFID:
                return tuple(raw_value)
            case SubKey.ASCII:
                return struct.unpack("c", raw_value)[0].decode("ascii")
            case SubKey.Digits:
                return tuple(raw_value)
            case SubKey.Digit:
                return raw_value[0]
            case SubKey.BitMask:
                return tuple(bool(v >> i & 0b1) for v in raw_value for i in range(8))
            case SubKey.Any:
                return raw_value
            case _:
                return None

    def fire_event(self, event: Event):
        print(f"{"Firing event:":<16}{event.source:<15} -> {event.name:<15} -> {str(event.value):<15} from {event.sender}")
        for key_func in self.POSSIBLE_EVENT_TYPES:
            source, name, value = key_func(event.source, event.name, event.value)
            listeners: list[Subscriber] = self.register.get(Condition(source, name, value), [])
            for listener in listeners:
                if not listener.allow_parallelism:
                    if listener.thread is not None and listener.thread.is_alive():
                        print("Cannot start thread: old thread is still alive.")
                        return
                print(f"{"Receiving event:":<16}{event.source:^15} -> {event.name:^15} -> {str(event.value):^15} -> {listener.callback.__name__:^15}")
                listener.thread = Thread(target=listener.callback, args=(event,), daemon=True)
                listener.thread.start()
                if listener.fire_once:
                    listeners.remove(listener)

    def receive(self, op_code: OpCode, ip: str, port: int, reply: Any) -> None:
        # print(f"Received {op_code} from {ip}:{port}")
        # for k, v in reply.items():
        #     print(f"\t{k} = {v}")

        sender = (ip, port)
        ts = time.time()

        self._parse_op(sender, ts, op_code, reply)

    def subscribe(self, callback: CallbackType, source: SourceNameType, event_name: EventNameType, condition_value: EventValueType = None, *, fire_once=False, allow_parallelism: bool=False):
        listener = Subscriber(callback, fire_once, allow_parallelism)
        condition = Condition(source, event_name, condition_value)
        if self.register.get(condition) is None:
            self.register[condition] = [listener, ]
        else:
            self.register[condition].append(listener)
        # print(f"registered condition {condition}")
