import pygame as pg
import threading
import app
import pygame_monitor


class GameManager:
    def __init__(self) -> None:
        self.button_is_pressed = False
        self.button_press_acknowledged = False
    
    def press_button():
        pass


if __name__ == "__main__":
    game_manager = GameManager()
    
    app.game_manager = game_manager
    flask_thread = threading.Thread(target=app.run_flask_app)
    flask_thread.start()
    
    pygame_monitor.game_manager = game_manager
    pygame_monitor.run(pg.FULLSCREEN)
    