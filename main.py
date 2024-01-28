import pygame as pg
import threading
from flask import Flask
from video_player import play_video


app = Flask(__name__)
button_is_pressed = False

def run_pygame():
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
                    play_video("media/video.mov")
                if event.key == pg.K_ESCAPE:
                    running = False
        
        screen.blit(pg.font.Font(pg.font.get_default_font(), 32).render('SPACE to play video', True, (192, 192, 192), None), (5, 5))
        if button_is_pressed:
            pg.draw.circle(screen, (255,255,255), (screen.get_width()/2, screen.get_height()/2), 50)
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(60)


@app.route('/button_pressed', methods=['GET'])
def button_pressed():
    global button_is_pressed
    button_is_pressed = True
    return "Button press acknowledged", 200


@app.route('/button_unpressed', methods=['GET'])
def button_unpressed():
    global button_is_pressed
    button_is_pressed = False
    return "Button unpress acknowledged", 200


def run_flask_app():
    app.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
    run_pygame()  
    






"""import pygame as pg
import cv2

video = cv2.VideoCapture("media/video.mov")
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
    
    if not paused:
        playing, video_image = video.read()
        if playing:
            video_surf = pg.image.frombuffer(
                video_image.tobytes(), video_image.shape[1::-1], "BGR")
        else:
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            playing = False
        window.blit(video_surf, (0, 0))
    
    pg.display.flip()

pg.quit()
exit()"""