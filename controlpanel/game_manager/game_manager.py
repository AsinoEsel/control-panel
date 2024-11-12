import pygame as pg
from .games import BaseGame
from controlpanel.shaders import Shaders
from .utils import get_output_size, get_display_flags


class GameManager:
    def __init__(self, resolution: tuple[int, int], is_fullscreen: bool, use_shaders: bool, stretch_to_fit: bool):
        pg.init()
        self.games: dict[str:BaseGame] = dict()
        self.current_game: BaseGame | None = None
        self.screen = pg.display.set_mode(get_output_size(resolution, is_fullscreen, use_shaders, stretch_to_fit),
                                          flags=get_display_flags(is_fullscreen, use_shaders))
        self.shaders: Shaders | None = Shaders(texture_sizes=[resolution,
                                                              (resolution[0]//2, resolution[1]//2),
                                                              (resolution[0]//2, resolution[1]//2)],
                                               shader_operations=[(1, "Downscale", {"_MainTex": 0}),
                                                                  (1, "Threshold", {"_MainTex": 1}),
                                                                  (1, "Blur_H", {"_MainTex": 1}),
                                                                  (1, "Blur_V", {"_MainTex": 1}),
                                                                  (2, "Ghost", {"_MainTex": 1, "_SecondaryTex": 2}),
                                                                  (0, "Add", {"_MainTex": 0, "_SecondaryTex": 2}),
                                                                  (0, "CRT", {"_MainTex": 0}),
                                                                  (-1, "To_BGRA", {"_MainTex": 0}),
                                                                  ]
                                               ) if use_shaders else None

    def add_game(self, game: BaseGame, *, make_current: bool = False):
        if self.games.get(game.name) is not None:
            raise ValueError(f"Game with name {game.name} already exists!")
        self.games[game.name] = game
        if make_current:
            self.current_game = game

    def run(self):
        clock = pg.time.Clock()
        dt: int = 0
        while True:

            if self.current_game is None:
                clock.tick(1)
                continue

            self.current_game.handle_events(pg.event.get())

            self.current_game.update(dt)

            self.current_game.render()

            if self.shaders:
                self.shaders.apply([self.current_game.screen,])
            else:
                pg.transform.scale(self.current_game.screen, self.screen.get_size(), self.screen)

            pg.display.flip()

            dt = clock.tick(self.current_game.tick_rate)
