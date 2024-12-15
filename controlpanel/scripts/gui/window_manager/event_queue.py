import time
from typing import Any, Generator, Callable


Event = Generator[None, None, None]
Callback = Callable[[], Any]


class Delay:
    """
    Iterable delay class that can be used in an asynchronous event to delay for an amount of time.
    Can be used like this to asynchronously delay by 1 second: yield from Delay(1)
        Note: this is equivalent to the following: for _ in Delay(1): yield
    An optional wait_callback can be specified, which will be called each tick while delaying.
    """

    def __init__(self, duration: float, wait_callback: Callback | None = None):
        self.duration = duration
        self.wait_callback = wait_callback
        self.start_time = time.time()

    def __iter__(self):
        while time.time() - self.start_time < self.duration:
            if self.wait_callback:
                self.wait_callback()
            yield


class EventQueue:
    """
    Encapsulates the asynchronous event handling by handling a single generated
    result per event per tick.
    """

    def __init__(self):
        self._events: list[Event] = []

    def update(self) -> None:
        """Updates the event queue"""
        expired_events: list[Event] = []
        for event in self._events:
            try:
                next(event)
            except StopIteration:
                expired_events.append(event)
        self._events = [x for x in self._events if x not in expired_events]

    def append(self, event: Event) -> None:
        """Appends the specified event to the event queue"""
        self._events.append(event)


event_queue = EventQueue()
