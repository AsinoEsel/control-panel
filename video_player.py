import pygame as pg
import cv2

def play_video(path: str, window_size: tuple[int, int]|None = None, repeats: int = 0):
    video = cv2.VideoCapture(path)
    playing, video_image = video.read()
    fps = video.get(cv2.CAP_PROP_FPS)

    if window_size is None:
        window_size = video_image.shape[1::-1]
    
    window = pg.display.set_mode(window_size)
    clock = pg.time.Clock()

    run = playing
    paused = False
    while run:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    paused = not paused
                if event.key == pg.K_ESCAPE:
                    run = False
        
        if paused:
            window.blit(pg.font.Font(pg.font.get_default_font(), 32).render('Paused. SPACE to unpause.', True, (192, 192, 192), None), (5, 5))
        else:
            playing, video_image = video.read()
            if not playing:
                video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                playing, video_image = video.read()
            video_surf = pg.image.frombuffer(video_image.tobytes(), video_image.shape[1::-1], "BGR")
            video_surf = pg.transform.scale(video_surf, window_size)

            window.blit(video_surf, (0, 0))
        
        pg.display.flip()
        clock.tick(fps)
    return


if __name__ == "__main__":
    pg.init()
    play_video("media/video.mov")