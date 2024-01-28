import pygame as pg
from video_player import play_video


game_manager = None

def run():
    pg.init()
    screen = pg.display.set_mode((1920, 1080))
    clock = pg.time.Clock()
    running = True
    while running:
        screen.fill((16,16,16))
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    play_video("media/video.mov", window_size=screen.get_size())
                if event.key == pg.K_ESCAPE:
                    running = False
        
        screen.blit(pg.font.Font(pg.font.get_default_font(), 32).render('SPACE to play video', True, (192, 192, 192), None), (5, 5))
        if game_manager.button_is_pressed:
            pg.draw.circle(screen, (255,255,255), (screen.get_width()/2, screen.get_height()/2), 50)
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(60)
        
if __name__ == "__main__":
    from main import GameManager
    game_manager = GameManager()
    run()