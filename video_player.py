import pygame as pg
import cv2

def play_video(path: str):
    video = cv2.VideoCapture(path)
    playing, video_image = video.read()
    fps = video.get(cv2.CAP_PROP_FPS)

    window = pg.display.set_mode(video_image.shape[1::-1])
    clock = pg.time.Clock()

    run = playing
    paused = False
    while run:
        clock.tick(fps)
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
            if playing:
                video_surf = pg.image.frombuffer(
                    video_image.tobytes(), video_image.shape[1::-1], "BGR")
            else:
                video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                playing = False
            window.blit(video_surf, (0, 0))
        
        pg.display.flip()
    return