import pygame as pg
from controlpanel.game_manager.dev_console import console_command


class BaseGame:
    def __init__(self,
                 name: str,
                 resolution: tuple[int, int],
                 *,
                 tickrate: float = 30.0,
                 timescale: float = 1.0
                 ):
        self.name = name
        self.screen = pg.surface.Surface(resolution)
        self._base_tickrate = tickrate
        self._tickrate = tickrate * timescale
        self._timescale = timescale
        self.is_running: bool = True
        self._dt: float = 1 / tickrate * timescale
        # self.fallback_shaders = Shaders([resolution], [(-1, "To_BGRA", {"_MainTex": 0})])
        # self.shaders = shaders if shaders is not None else self.fallback_shaders

    @property
    def tickrate(self) -> float:
        return self._tickrate

    @property
    def timescale(self) -> float:
        return self._timescale

    @timescale.setter
    def timescale(self, new_timescale: float):
        self._timescale = new_timescale
        self._tickrate = self._base_tickrate * new_timescale

    @console_command(is_cheat_protected=True)
    def set_timescale(self, timescale: float):
        self.timescale = timescale

    @property
    def dt(self) -> float:
        return self._dt

    def handle_events(self, events: list[pg.event.Event]) -> None:
        pass

    def update(self) -> None:
        pass

    def render(self) -> None:
        pass

    def standalone_run(self):
        import argparse
        parser = argparse.ArgumentParser(description=self.name)
        parser.add_argument('-w', '--windowed', action='store_true', help='Run in windowed mode (fullscreen is default)')
        args = parser.parse_args()

        pg.init()
        self.screen = pg.display.set_mode(self.screen.get_size(), pg.FULLSCREEN if not args.windowed else 0)
        clock = pg.time.Clock()
        while True:
            self.handle_events(pg.event.get())
            self.update()
            self.render()

            pg.display.flip()
            self._dt = clock.tick(self._tickrate) / 1000 * self._timescale
