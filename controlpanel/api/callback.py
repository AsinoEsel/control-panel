from typing import Iterable, Hashable, Callable, Union, TypeVar
from controlpanel.event_manager import Event
from itertools import product
from .api import subscribe


T = TypeVar('T', bound=Hashable)


def callback(*,
    source: str | Iterable[str] | None = None,
    action: str | Iterable[str] | None = None,
    value: Hashable | Iterable[Hashable] | None = None,
    fire_once: bool = False,
    allow_parallelism: bool = False,
    ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:

    def normalize(x: Union[str, T, Iterable[T], None]) -> list[T] | list[None]:
        if x is None:
            return [None]
        if isinstance(x, str) or not isinstance(x, Iterable):
            return [x]
        return list(x)

    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        sources = normalize(source)
        actions = normalize(action)
        values = normalize(value)

        for s, a, v in product(sources, actions, values):
            subscribe(func, s, a, v,
                      fire_once=fire_once,
                      allow_parallelism=allow_parallelism)
        return func

    return decorator
