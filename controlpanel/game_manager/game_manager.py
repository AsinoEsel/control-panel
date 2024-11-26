import pygame as pg
from .games import BaseGame
from controlpanel.shaders import Shaders
from .dev_console import DeveloperConsole, console_command
from .utils import get_output_size, get_display_flags


class GameManager:
    def __init__(self, resolution: tuple[int, int], is_fullscreen: bool, use_shaders: bool, stretch_to_fit: bool):
        pg.init()
        self.games: dict[str:BaseGame] = dict()
        self.current_game: BaseGame | None = None
        self.screen = pg.display.set_mode(get_output_size(resolution, is_fullscreen, use_shaders, stretch_to_fit),
                                          flags=get_display_flags(is_fullscreen, use_shaders))
        self.use_shaders = use_shaders
        self.dev_console = DeveloperConsole(self, self.screen)
        self.running = True

    def add_game(self, game: BaseGame, make_current: bool = False):
        if self.games.get(game.name) is not None:
            raise ValueError(f"Game with name {game.name} already exists!")
        self.games[game.name] = game
        if make_current:
            self.current_game = game

    @console_command("toggleconsole")
    def toggle_dev_console(self):
        self.dev_console.open = not self.dev_console.open

    @console_command("exit")
    def quit(self):
        self.running = False

    def run(self):
        if self.current_game is None and self.games:
            self.current_game = list(self.games.values())[0]

        clock = pg.time.Clock()
        while self.running:

            if self.current_game is None:
                self.screen.fill((100, 100, 100))
                pg.display.flip()
                pg.event.pump()
                clock.tick(1)
                continue

            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    pg.quit()
                elif event.type == pg.KEYDOWN and event.key == pg.K_CARET:
                    self.dev_console.open = not self.dev_console.open

            if self.dev_console.open:
                self.dev_console.handle_events(events)
            else:
                self.current_game.handle_events(events)

            self.current_game.update()

            self.current_game.render()

            if self.use_shaders:
                self.current_game.shaders.apply([self.current_game.screen,])
            else:
                pg.transform.scale(self.current_game.screen, self.screen.get_size(), self.screen)
                if self.dev_console.open:
                    self.dev_console.render(self.screen)

            pg.display.flip()

            self.current_game._dt = clock.tick(self.current_game.tickrate) / 1000 * self.current_game.timescale

        pg.quit()
