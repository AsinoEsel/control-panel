import pygame as pg
from controlpanel.game_manager import BaseGame


class ExampleGame(BaseGame):
    def __init__(self):
        super().__init__("ExampleGame", (1920, 1080), tickrate=30)
        self.color = (255, 0, 0)  # example. Game variables go here.

    def handle_events(self, events: list[pg.event.Event]) -> None:
        """Key presses, mouse movements, and other pygame events are processed here.
        Executed once at the start of every tick."""
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
            elif event.type == pg.KEYDOWN:
                ...  # key press events are processed here

    def update(self) -> None:
        """Game logic happens here. Executed once every tick."""
        ...

    def render(self) -> None:
        """Rendering logic happens here. Executed at the end of every tick.
        Final image is stored in the self.screen surface."""
        self.screen.fill(self.color)  # example


if __name__ == "__main__":
    pg.init()
    my_game = ExampleGame()
    my_game.screen = pg.display.set_mode(my_game.screen.get_size(), pg.FULLSCREEN)
    my_game.standalone_run()
