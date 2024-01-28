import pygame as pg
import cv2
import numpy as np

def screen_composit(frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
    
    # Normalize pixel values to 0 to 1  
    normalized_frame1 = frame1 / 255.0
    normalized_frame2 = frame2 / 255.0
    
    # Invert pixel values
    inverted_frame1 = cv2.subtract(1.0, normalized_frame1)
    inverted_frame2 = cv2.subtract(1.0, normalized_frame2)

    # Multiply inverted frames
    multiplied_composit = cv2.multiply(inverted_frame1, inverted_frame2)
    
    # Invert the result
    inverted_composit = cv2.subtract(1.0, multiplied_composit)
    
    # denormalize
    denormalized_composit = (255 * inverted_composit).astype(np.uint8)
    
    return denormalized_composit


def blend(frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
    # Create an alpha channel with fully opaque values (1)
    alpha_channel = np.ones((frame1.shape[0], frame1.shape[1], 1), dtype=np.uint8)

    # Concatenate the original RGB array with the alpha channel
    frame1 = np.concatenate((frame1, alpha_channel), axis=2)
    frame2 = np.concatenate((frame2, alpha_channel), axis=2)

    from blend_modes import soft_light
    blended_image = soft_light(frame1, frame2, 1)
    
    return blended_image[:, :, :3]
    
    

def play_video(path: str, window_size: tuple[int, int]|None = None, repeats: int = 0):
    video = cv2.VideoCapture(path)
    overlay = cv2.VideoCapture("media/vhs_overlay_playing.mp4")
    playing, video_image = video.read()
    fps = video.get(cv2.CAP_PROP_FPS)

    if window_size is None:
        window_size = video_image.shape[1::-1]
    
    window = pg.display.set_mode(window_size)
    clock = pg.time.Clock()

    run = playing
    state = "playing"
    while run:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    state = "playing" if state == "paused" else "paused"
                if event.key == pg.K_ESCAPE:
                    run = False
        
        match state:
            case "playing":
                playing, video_image = video.read()
                if not playing:
                    if repeats == 0:
                        return
                    repeats -= 1
                    video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    playing, video_image = video.read()
                
                
                # composit = blend(video_image.astype(float), overlay_image.astype(float)).astype(np.uint8)
                
                video_surf = pg.image.frombuffer(video_image.tobytes(), video_image.shape[1::-1], "BGR")
                video_surf = pg.transform.scale(video_surf, window_size)
                window.blit(video_surf, (0, 0))
            case "paused":
                _, overlay_image = overlay.read()
                composit = screen_composit(video_image, overlay_image)
                video_surf = pg.image.frombuffer(composit.tobytes(), composit.shape[1::-1], "BGR")
                video_surf = pg.transform.scale(video_surf, window_size)
                window.blit(video_surf, (0, 0))
                window.blit(pg.font.Font(pg.font.get_default_font(), 32).render('Paused. SPACE to unpause.', True, (192, 192, 192), None), (5, 5))
        
        pg.display.flip()
        clock.tick(fps)
    return


if __name__ == "__main__":
    pg.init()
    play_video("media/video.mov", repeats=-1)