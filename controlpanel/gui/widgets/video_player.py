from .widget import Widget
import pygame as pg
import cv2
from controlpanel.gui.window_manager.window_manager_setup import TARGET_FRAME_RATE


class VideoPlayer(Widget):
    def __init__(self, name: str, parent: Widget, x, y, w, h, video_path: str) -> None:
        super().__init__(name, parent, x, y, w, h, None)
        self.video = cv2.VideoCapture(video_path)
        self.playing, self.video_image = self.video.read()
        self.paused = False
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.paused = not self.paused
        return super().handle_event(event)

    def render_body(self):
        if self.playing:
            video_surf = pg.image.frombuffer(self.video_image.tobytes(), self.video_image.shape[1::-1], "BGR")
            video_surf = pg.transform.scale(video_surf, self.surface.get_size())
            self.surface.blit(video_surf, (0, 0))

    def advance_video(self):
        self.playing, self.video_image = self.video.read()
        if not self.playing:
            return
        self.flag_as_needing_rerender()
    
    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        if not self.playing:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.advance_video()
            self.paused = True
        frame = tick * self.fps // TARGET_FRAME_RATE
        if frame > self.current_frame and not self.paused:
            self.advance_video()
            self.current_frame = frame
