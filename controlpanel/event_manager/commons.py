from dataclasses import dataclass
from typing import Callable
from threading import Thread
import pygame as pg
from collections.abc import Hashable

# Atomic numbers: iron = 26, oxygen = 8
# Iron(II) oxide (FeO): 32 protons
# Iron(III) oxide (Fe22O3): 76 protons
KEY_CONTROL_PANEL_PROTOCOL = 76
CONTROL_PANEL_EVENT = pg.event.custom_type()


EventSourceType = str
EventActionType = str
EventValueType = Hashable | None


@dataclass(frozen=True)
class Event:
    source: EventSourceType
    action: EventActionType
    value: EventValueType
    sender: tuple[str, int] | None
    timestamp: float


@dataclass(frozen=True)
class Condition:
    source: EventSourceType
    action: EventActionType
    value: EventValueType


CallbackType = Callable[[Event], None]


@dataclass
class Subscriber:
    callback: CallbackType
    fire_once: bool = False
    allow_parallelism: bool = False
    thread: Thread | None = None
