from enum import IntEnum
from dataclasses import dataclass
from typing import Callable
from threading import Thread
import pygame as pg

# Atomic numbers: iron = 26, oxygen = 8
# Iron(II) oxide (FeO): 32 protons
# Iron(III) oxide (Fe22O3): 76 protons
KEY_CONTROL_PANEL_PROTOCOL = 76
CONTROL_PANEL_EVENT = pg.event.custom_type()


class SubKey(IntEnum):
    PushButton = 0
    RotaryEncoder = 1
    Integer = 2  # 32 bit
    String = 3  # null-terminated
    Double = 4  # 64 bit
    RFID = 5  # UID n bits -> int array
    ASCII = 6  # 8 bit
    Digits = 7  # 8 bit: 0-9
    BitMask = 8  # n bits -> bool array
    Digit = 9  # 8 bit: 0-9
    BananaPlugs = 10  # 2 times 8 bit -> tuple[int, int]
    Any = 255  # n bits raw bytearray

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
