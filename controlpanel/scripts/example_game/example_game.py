import pygame as pg
from controlpanel.game_manager import BaseGame


class ExampleGame(BaseGame):
    def __init__(self):
        super().__init__("Example Game", (1920, 1080), tickrate=30)
        self.color = (255, 0, 0)  # example

    def handle_events(self, events: list[pg.event.Event]) -> None:
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
            elif event.type == pg.KEYDOWN:
                ...

    def update(self) -> None:
        pass

    def render(self) -> None:
        self.screen.fill(self.color)  # example


if __name__ == "__main__":
    pg.init()
    my_game = ExampleGame()
    my_game.screen = pg.display.set_mode(my_game.screen.get_size(), pg.FULLSCREEN)
    my_game.standalone_run()
