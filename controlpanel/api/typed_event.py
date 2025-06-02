from dataclasses import dataclass
from typing import Generic, TypeVar
from controlpanel.event_manager import EventSourceType, EventActionType


T = TypeVar("T")


@dataclass(frozen=True)
class TypedEvent(Generic[T]):
    source: EventSourceType
    action: EventActionType
    value: T
    sender: tuple[str, int] | None
    timestamp: float
