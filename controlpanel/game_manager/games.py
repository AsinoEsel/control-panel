import pygame as pg


class BaseGame:
    def __init__(self, name: str, resolution: tuple[int, int], tick_rate: int = 60):
        self.name = name
        self.screen = pg.surface.Surface(resolution)
        self.tick_rate = tick_rate
        self.is_running: bool = True

    def handle_events(self, events: list[pg.event.Event]) -> None:
        pass

    def update(self, dt: int) -> None:
        pass

    def render(self) -> None:
        pass
