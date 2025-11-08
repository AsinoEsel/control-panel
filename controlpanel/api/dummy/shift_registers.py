import asyncio
from controlpanel.shared.base.shift_registers import BasePisoShiftRegister, BaseSipoShiftRegister
from .sensor import Sensor
from .fixture import Fixture
from artnet import ArtNet
from typing import Callable, SupportsIndex
import random
from .esp32 import ESP32


class _States:
    """A proxy class for the states list.
    Automatically calls the update_callback function when a value in the list is changed."""
    def __init__(self, states: list[bool], update_callback: Callable[[], None]):
        self._states = states
        self._update_callback = update_callback

    def __getitem__(self, key):
        return self._states[key]

    def __setitem__(self, key, value):
        self._states[key] = value
        self._update_callback()

    def __len__(self):
        return len(self._states)

    def __iter__(self):
        return iter(self._states)

    def __repr__(self):
        return repr(self._states)

    def __getslice__(self, i, j):
        return self._states[i:j]

    def __setslice__(self, i, j, sequence):
        self._states[i:j] = sequence
        self._update_callback()

    def __eq__(self, other):
        return self._states == other



class PisoShiftRegister(BasePisoShiftRegister, Sensor):
    EVENT_TYPES = {
        "ButtonsChanged": tuple[tuple[int, bool], ...],
    }

    def __init__(self, _artnet: ArtNet, name: str, count: int):
        Sensor.__init__(self, _artnet, name)
        self._states: list[bool] = [False for _ in range(count * 8)]

    def __getitem__(self, key):
        return self._states[key]

    def __len__(self):
        return len(self._states)

    def __iter__(self):
        return iter(self._states)

    @property
    def states(self):
        return tuple(self._states)

    def parse_trigger_payload(self, data: bytes) -> tuple[str, tuple[tuple[int, bool], ...]]:
        assert len(data) % 2 == 0, "data must be of even length"
        assert len(data) <= 2 * len(self._states), "length of data is too long"
        updates: list[tuple[int, bool]] = []
        for i in range(0, len(data), 2):
            index: int = data[i]
            value: bool = not bool(data[i + 1])
            updates.append((index, value))
            self._states[index] = value

        return "ButtonsChanged", tuple(updates)


class SipoShiftRegister(BaseSipoShiftRegister, Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 name: str,
                 count: int,
                 *,
                 universe: int | None = None):
        Fixture.__init__(self, _artnet, _loop, _esp, name, universe=universe)
        self._states: _States = _States([False for _ in range(count * 8)], self.send_dmx)

    def send_dmx(self):
        self._send_dmx_packet(bytearray(self._states))

    def __len__(self):
        return len(self._states)

    def __getitem__(self, item) -> bool:
        return self._states[item]

    def __setitem__(self, index: SupportsIndex, value: bool) -> None:
        self.set_state(index, value)

    def __iter__(self):
        return iter(self._states)  # returns an iterator

    @property
    def states(self) -> _States:
        return self._states

    @states.setter
    def states(self, new_states: list[bool]):
        if not isinstance(new_states, list):
            raise TypeError("States must be assigned a list of booleans.")
        if len(new_states) != len(self):
            raise ValueError(f"State list must be exactly {len(self)} items long.")
        self._states[:] = [bool(state) for state in new_states]  # Update the existing States proxy in-place so references don't break

    def set_state(self, index: SupportsIndex, value: bool):
        self._states[index] = bool(value)
        self.send_dmx()

    def set_states(self, states: list[bool]):
        self.states = states

    def turn_on(self, state: SupportsIndex):
        self.states[state] = True

    def turn_off(self, state: SupportsIndex):
        self.states[state] = False

    def flip(self, state: SupportsIndex):
        self.states[state] = not self.states[state]

    def randomize(self, weight: float = 0.5):
        weight = min(1.0, max(0.0, weight))
        for i in range(len(self._states)):
            self._states[i] = random.random() < weight
        self.send_dmx()

    def whiteout(self) -> None:
        for i in range(len(self._states)):
            self._states[i] = True
        self.send_dmx()

    def blackout(self) -> None:
        for i in range(len(self._states)):
            self._states[i] = False
        self.send_dmx()
