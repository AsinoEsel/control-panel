import pygame as pg
import os
import cv2
from pygame.event import Event
import utils
from window_manager_setup import *
import debug_util
import time
from shaders import Shaders

from widgets import Widget, STLRenderer, Desktop, Window, InputBox, Radar, TextField, Image, Log, Terminal


class WindowManager:
    def __init__(self, control_panel, *, fullscreen: bool = False, use_shaders: bool = True, maintain_aspect_ratio: bool = True):
        self.control_panel: ControlPanel = control_panel
        self.fullscreen = fullscreen
        self.use_shaders = use_shaders
        flags = pg.FULLSCREEN if fullscreen else 0
        if use_shaders:
            flags |= pg.OPENGL | pg.DOUBLEBUF
        if not fullscreen:
            self.output_size = RENDER_SIZE            
        if fullscreen and maintain_aspect_ratio:
            self.output_size = utils.scale_resolution(RENDER_SIZE, (pg.display.Info().current_w, pg.display.Info().current_h))
        elif fullscreen and not maintain_aspect_ratio:
            self.output_size = (pg.display.Info().current_w, pg.display.Info().current_h)
        self.screen = pg.display.set_mode(self.output_size, flags=flags)
        self.desktops = [Desktop(control_panel) for _ in range(4)]
        self.desktop = self.desktops[0]
        self.set_up_desktops(self.desktops)

        
    def change_desktop(self, index: int):
        if not 0 <= index < len(self.desktops):
            return
        self.desktop = self.desktops[index]
        
        
    def set_up_desktops(self, desktops: list['Desktop']):
        desktop = desktops[0]
        desktop.add_element(terminal := Terminal(desktop, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT-2*DEFAULT_GAP))
        desktop.add_element(log := Log(desktop, x=RENDER_WIDTH//2+DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP))
        empty_widget = Widget(desktop, x=RENDER_WIDTH//2+DEFAULT_GAP, y=RENDER_HEIGHT//2+DEFAULT_GAP, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP)
        image = Image(desktop, x=RENDER_WIDTH//2+DEFAULT_GAP, y=RENDER_HEIGHT//2+DEFAULT_GAP, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP,
                      image_path=os.path.join('media', 'robot36.png'))
        text_field = TextField(desktop, x=RENDER_WIDTH//2+DEFAULT_GAP, y=RENDER_HEIGHT//2+DEFAULT_GAP, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP,
                               text=os.path.join('media','roboter_ascii.txt'), load_ascii_file=True, transparent=False, font=SMALL_FONT)
        desktop.add_element(STLRenderer(desktop, "media/fox_centered.stl", x=RENDER_WIDTH//2+DEFAULT_GAP, y=RENDER_HEIGHT//2+DEFAULT_GAP,
                                   w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP))
        desktop.terminal = terminal
        # desktop.add_element(Taskbar(desktop, 20))
        log.print_to_log("ROTER TEXT", (255,0,0))
        
        desktop2 = desktops[1]
        desktop2.add_element(Radar(desktop2, png='media/red_dot_image.png'))
        
        desktop3 = desktops[2]
        from widgets import LaserGame
        desktop3.add_element(LaserGame(desktop3))
        
        desktop4 = desktops[3]

    
    def run(self):
        pg.init()
        clock = pg.time.Clock()
        tick = 0
        dt = 0
        
        joysticks = {}
        
        if self.use_shaders:
            shaders = Shaders(texture_sizes=[RENDER_SIZE, QUARTER_RENDER_SIZE, QUARTER_RENDER_SIZE],
                              shader_operations=[(1, "Downscale", {"_MainTex": 0}),
                                                  (1, "Threshold", {"_MainTex": 1}),
                                                  (1, "Blur_H", {"_MainTex": 1}),
                                                  (1, "Blur_V", {"_MainTex": 1}),
                                                  (2, "Ghost", {"_MainTex": 1, "_SecondaryTex": 2}),
                                                  (0, "Add", {"_MainTex": 0, "_SecondaryTex": 2}),
                                                  (0, "CRT", {"_MainTex": 0}),
                                                  (-1, "To_BGRA", {"_MainTex": 0}),
                                                  ])
        
        if self.fullscreen:
            scaling_ratio = (RENDER_WIDTH/self.output_size[0], RENDER_HEIGHT/self.output_size[1])
        
        while True:
            tick += 1
            current_time = time.time()
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                if event.type == pg.JOYDEVICEADDED:
                    joy = pg.joystick.Joystick(event.device_index)
                    joysticks[joy.get_instance_id()] = joy
                    print(f"Joystick {joy.get_instance_id()} connected")
                if pg.key.get_mods() & pg.KMOD_CTRL and event.type == pg.KEYDOWN and pg.K_0 <= event.key <= pg.K_9:
                    self.change_desktop(event.key - pg.K_0 - 1)
                    continue
                if self.fullscreen and event.type in (pg.MOUSEMOTION, pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
                    event.pos = (event.pos[0] * scaling_ratio[0], event.pos[1] * scaling_ratio[1])
                    if event.type == pg.MOUSEMOTION:
                        event.rel = (event.rel[0] * scaling_ratio[0], event.rel[1] * scaling_ratio[1])
                self.desktop.handle_event(event)
            
            # for future in self.control_panel.futures:
            #     if future.done():
            #         if isinstance((error := future.result()), Exception):
            #             self.desktop.terminal.log.print_to_log(str(error), (255,0,0))
            #             self.control_panel.futures.remove(future)
            #             continue
            #         try:
            #             json = future.result().json()
            #             self.desktop.terminal.log.print_to_log(f"{json["status"]}: {json["message"]}")
            #         except ConnectTimeout as e:
            #             self.desktop.terminal.log.print_to_log(str(e), (255,0,0))
            #         self.control_panel.futures.remove(future)
            
            self.desktop.propagate_update(tick, dt=dt, joysticks=joysticks)
            
            mouse_pos = pg.mouse.get_pos()
            if self.fullscreen:
                mouse_pos = (mouse_pos[0] * scaling_ratio[0], mouse_pos[1] * scaling_ratio[1])
            
            if self.use_shaders:
                shaders.apply(self.desktop.surface, current_time)
            else:
                if self.fullscreen:
                    pg.transform.scale(self.desktop.surface, self.output_size, self.screen)
                else:
                    self.screen.blit(self.desktop.surface, (0,0))
            
            pg.event.pump()
            pg.display.flip()
            dt = clock.tick(TARGET_FRAME_RATE)
                
        
if __name__ == "__main__":
    from control_panel import ControlPanel
    import threading
    control_panel = ControlPanel(fullscreen=True, use_shaders=True, maintain_aspect_ratio=True)
    window_manager_thread = threading.Thread(target=control_panel.window_manager.run)
    window_manager_thread.run()