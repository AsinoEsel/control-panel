import pygame as pg


class BaseGame:
    def __init__(self,
                 name: str,
                 resolution: tuple[int, int],
                 *,
                 tick_rate: int = 30,
                 ):
        self.name = name
        self.screen = pg.surface.Surface(resolution)
        self.tick_rate = tick_rate
        self.is_running: bool = True
        # self.fallback_shaders = Shaders([resolution], [(-1, "To_BGRA", {"_MainTex": 0})])
        # self.shaders = shaders if shaders is not None else self.fallback_shaders

    def handle_events(self, events: list[pg.event.Event]) -> None:
        pass

    def update(self, dt: int) -> None:
        pass

    def render(self) -> None:
        pass

    def standalone_run(self):
        dt = 1
        clock = pg.time.Clock()
        while True:
            self.handle_events(pg.event.get())
            self.update(dt)
            self.render()

            pg.display.flip()
            dt = clock.tick(self.tick_rate)
