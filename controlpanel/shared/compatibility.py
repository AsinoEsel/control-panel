"""This is where we define functions that are recognized on one platform but not the other,
for maximum cross-platform compatibility
"""


try:
    from micropython import const
except ImportError:
    from typing import TypeVar
    T = TypeVar("T")
    def const(x: T) -> T:
        return x


try:
    from abc import abstractmethod
except ImportError:
    def abstractmethod(func):
        return func


try:
    from time import ticks_ms
except ImportError:
    from time import time
    def ticks_ms() -> int:
        return int(time() * 1000)


try:
    from artnet import ArtNet
except ImportError:
    from controlpanel.upy.artnet import ArtNet
