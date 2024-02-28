import pygame as pg
import os
import cv2
from pygame.event import Event
from utils import *
from window_manager_setup import *
import stl_renderer as stlr
from console_commands import handle_user_input
import debug_util
import time
from shaders import Shaders
from requests.exceptions import ConnectTimeout
import radar
from cursor import cursor_surface


class WindowManager:
    def __init__(self, control_panel, *, fullscreen: bool = False, use_shaders: bool = True, maintain_aspect_ratio: bool = True):
        self.control_panel: ControlPanel = control_panel
        flags = pg.FULLSCREEN if fullscreen else 0
        if use_shaders:
            flags |= pg.OPENGL | pg.DOUBLEBUF
        if not fullscreen:
            output_size = RENDER_SIZE            
        if fullscreen and maintain_aspect_ratio:
            output_size = scale_resolution(RENDER_SIZE, (pg.display.Info().current_w, pg.display.Info().current_h))
        elif fullscreen and not maintain_aspect_ratio:
            output_size = (pg.display.Info().current_w, pg.display.Info().current_h)
        self.screen = pg.display.set_mode(output_size, flags=flags)
        self.desktops = [Desktop(control_panel), Desktop(control_panel)]
        self.desktop = self.desktops[1]
        self.set_up_desktops(self.desktops)
        self.run(output_size, fullscreen=fullscreen, use_shaders=use_shaders)
    
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
        desktop.add_element(LoginWindow(desktop))
        desktop.terminal = terminal
        log.print_to_log("ROTER TEXT", (255,0,0))
        
        desktop2 = desktops[1]
        desktop2.add_element(Radar(desktop2, png='media/red_dot_image.png'))
    
    def run(self, output_size: tuple[int,int], fullscreen: bool, use_shaders: bool):
        pg.init()
        clock = pg.time.Clock()
        tick = 0
        dt = 0
        
        if use_shaders:
            shaders = Shaders(texture_sizes=[RENDER_SIZE, QUARTER_RENDER_SIZE, QUARTER_RENDER_SIZE],
                              surfaces_ints=[(self.desktop.surface, 0)],
                              shader_operations_todo=[(1, "Downscale", {"_MainTex": 0}),
                                                      (1, "Threshold", {"_MainTex": 1}),
                                                      (1, "Blur_H", {"_MainTex": 1}),
                                                      (1, "Blur_V", {"_MainTex": 1}),
                                                      (2, "Ghost", {"_MainTex": 1, "_SecondaryTex": 2}),
                                                      (0, "Add", {"_MainTex": 0, "_SecondaryTex": 2}),
                                                      (0, "CRT", {"_MainTex": 0}),
                                                      (-1, "To_BGRA", {"_MainTex": 0}),
                                                      ])
            shaders.compile_shaders()
        
        if fullscreen:
            scaling_ratio = (RENDER_WIDTH/output_size[0], RENDER_HEIGHT/output_size[1])
        
        while True:
            tick += 1
            current_time = time.time()
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                if pg.key.get_mods() & pg.KMOD_CTRL and event.type == pg.KEYDOWN and pg.K_0 <= event.key <= pg.K_9:
                    self.change_desktop(event.key - pg.K_0 - 1)
                    continue
                if fullscreen and event.type in (pg.MOUSEMOTION, pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP, pg.MOUSEWHEEL):
                    event.pos = (event.pos[0] * scaling_ratio[0], event.pos[1] * scaling_ratio[1])
                    if event.type == pg.MOUSEMOTION:
                        event.rel = (event.rel[0] * scaling_ratio[0], event.rel[1] * scaling_ratio[1])
                self.desktop.handle_event(event)
            
            for future in self.control_panel.futures:
                if future.done():
                    if isinstance((error := future.result()), Exception):
                        self.desktop.terminal.log.print_to_log(str(error), (255,0,0))
                        self.control_panel.futures.remove(future)
                        continue
                    try:
                        json = future.result().json()
                        self.desktop.terminal.log.print_to_log(f"{json["status"]}: {json["message"]}")
                    except ConnectTimeout as e:
                        self.desktop.terminal.log.print_to_log(str(e), (255,0,0))
                    self.control_panel.futures.remove(future)
            
            self.desktop.propagate_update(tick, dt=dt)
            
            mouse_pos = pg.mouse.get_pos()
            if fullscreen:
                mouse_pos = (mouse_pos[0] * scaling_ratio[0], mouse_pos[1] * scaling_ratio[1])
            self.desktop.surface.blit(cursor_surface, mouse_pos)
            
            if use_shaders:
                shaders.apply(current_time)
            else:
                if fullscreen:
                    pg.transform.scale(self.desktop.surface, output_size, self.screen)
                else:
                    self.screen.blit(self.desktop.surface, (0,0))
            
            pg.event.pump()
            pg.display.flip()
            dt = clock.tick(TARGET_FRAME_RATE)


class Widget:
    def __init__(self, parent, x, y, w, h, elements: list['Widget']|None = None) -> None:
        if elements is None:
            elements = []
        self.parent = parent
        self.position = pg.Vector2(x, y)
        self.rect = pg.Rect(0, 0, w, h)
        self.surface = pg.Surface((w, h))
        self.surface.fill(DEBUG_COLOR)
        self.active = False
        self.color = COLOR_INACTIVE
        self.accent_color = ACCENT_COLOR_INACTIVE
        self.elements = elements if elements else []
        self.active_element = elements[0] if elements else None
        self.needs_reblit = True
        self.needs_rerender = True
    
    def add_element(self, element: 'Widget', make_active_element: bool = False):
        self.elements.append(element)
        if make_active_element or not self.active_element:
            self.active_element = element
    
    def close_window(self, window: 'Window'):
        self.elements.remove(window)
        if self.active_element is window:
            if self.elements:
                self.active_element = self.elements[0]
                self.active_element.activate()
            else:
                self.active_element = None
        self.flag_as_needing_rerender()
    
    def get_root(self) -> 'Desktop':
        current = self
        while current.parent:
            current = current.parent
        return current

    def update(self, tick: int, dt: int):
        pass
    
    def propagate_update(self, tick: int, dt: int):
        self.update(tick, dt)
        for element in self.elements:
            element.propagate_update(tick, dt)
        if self.needs_rerender:
            self.render()
            self.needs_rerender = False
        if self.needs_reblit:
            self.blit_from_children()
            self.needs_reblit = False
    
    def next_element(self):
        self.active_element.deactivate()
        index = self.elements.index(self.active_element)
        index += 1
        if index >= len(self.elements):
            self.active_element = self.elements[0]
            if self.parent:
                self.parent.next_element()
            else:
                self.active_element.activate()
        else:
            self.active_element = self.elements[index]
            self.active_element.activate()
    
    def handle_event(self, event: Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            #  print(f"Handling event in {self}: {[element.title for element in self.elements if isinstance(element, Window)]}")
            event.pos = event.pos - self.position
            for element in reversed(self.elements):
                if pg.Rect(element.position, element.rect.size).collidepoint(event.pos):
                    if self.active_element:
                        self.active_element.deactivate()
                    self.active_element = element
                    self.active_element.activate()
                    element.handle_event(event)
                    return
            if self.active_element:
                self.active_element.deactivate()
                self.active_element = None
        if self.active_element:
            self.active_element.handle_event(event)
            return
        if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
            if not self.active_element and self.elements:
                self.active_element = self.elements[0]
                self.active_element.activate()
            else:
                self.parent.next_element()
    
    def activate(self) -> None:
        self.active = True
        self.color = COLOR_ACTIVE
        self.accent_color = ACCENT_COLOR_ACTIVE
        if self.active_element:
            self.active_element.activate()
        self.flag_as_needing_rerender()
    
    def deactivate(self) -> None:
        self.active = False
        self.color = COLOR_INACTIVE
        self.accent_color = ACCENT_COLOR_INACTIVE
        if self.active_element:
            self.active_element.deactivate()
        self.flag_as_needing_rerender()
    
    def flag_as_needing_rerender(self):
        self.needs_rerender = True
        node = self.parent
        while node:
            node.needs_reblit = True
            node = node.parent
    
    def blit_to_parent(self):
        self.parent.surface.blit(self.surface, self.position)
    
    def blit_from_children(self):
        for element in self.elements:
            self.surface.blit(element.surface, element.position)
    
    def render_border(self, thickness=LINE_THICKNESS_THIN):
        pg.draw.rect(self.surface, self.color, self.rect, thickness)
    
    def render(self) -> None:
        self.surface.fill(self.accent_color)
        pg.draw.rect(self.surface, self.color, self.rect, LINE_THICKNESS_THIN)
        self.blit_from_children()


class Desktop(Widget):
    def __init__(self, control_panel) -> None:
        self.control_panel: ControlPanel = control_panel
        super().__init__(None, 0, 0, RENDER_WIDTH, RENDER_HEIGHT)
        self.clipboard = ""
        
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.blit_from_children()
    
    def blit_to_parent(self):
        pass
    
    def add_video_window(self, video_path: str, window_title: str = "Video"):
        video_window = Window(self, window_title, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP)
        video = Video(video_window, x=video_window.inner_rect.left, y=video_window.inner_rect.top, w=video_window.inner_rect.w, h=video_window.inner_rect.h,
                      video_path=video_path)
        video_window.add_element(video)
        self.add_element(video_window)
            

class Window(Widget):
    def __init__(self, parent, title: str, w: int, h: int, text: str|None = None, x: int|None = None, y: int|None = None, font=DEFAULT_FONT) -> None:
        x = parent.rect.w//2 - w//2 if x is None else x
        y = parent.rect.h//2 - h//2 if y is None else y
        super().__init__(parent, x, y, w, h)
        self.inner_rect = pg.Rect(DEFAULT_GAP, CHAR_HEIGHT[font] + DEFAULT_GAP,
                                  w - 2*DEFAULT_GAP, h - CHAR_HEIGHT[font] - 2*DEFAULT_GAP)
        self.font = font
        self.title = title
        if text:
            self.elements.append(TextField(self, self.inner_rect.left + DEFAULT_GAP, self.inner_rect.top + DEFAULT_GAP, 
                                           self.inner_rect.width - 2*DEFAULT_GAP, self.inner_rect.height//2, text, True))

    
    def handle_event(self, event: Event):
        if event.type == pg.MOUSEMOTION:
            if event.buttons[0] and self.rect.collidepoint(self.global_to_local_position((event.pos[0]-event.rel[0], event.pos[1]-event.rel[1]))):
                self.position += pg.Vector2(event.rel)
                self.position.x = max(0, self.position.x)
                self.position.x = min(self.parent.surface.get_width()-self.rect.w, self.position.x)
                self.position.y = max(0, self.position.y)
                self.position.y = min(self.parent.surface.get_height()-self.rect.h, self.position.y)
                self.parent.flag_as_needing_rerender()
            return
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.close()
                return
        super().handle_event(event)
    
    def global_to_local_position(self, position):
        current = self
        while current.parent is not None:
            position -= current.position
            current = current.parent
        return position
    
    def go_to_foreground(self):
        self.parent.elements.remove(self)
        self.parent.elements.append(self)
        
    def close(self):
        self.parent.close_window(self)
    
    def render_title(self):
        self.surface.blit(self.font.render(self.title, True, self.color), (DEFAULT_GAP, DEFAULT_GAP))
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.render_title()
        pg.draw.rect(self.surface, self.color, self.rect, LINE_THICKNESS_THIN)
        pg.draw.rect(self.surface, ACCENT_COLOR_INACTIVE, self.inner_rect)
        pg.draw.rect(self.surface, self.color, self.inner_rect, LINE_THICKNESS_THIN)
        self.blit_from_children()


class LoginWindow(Window):
    def __init__(self, parent) -> None:
        super().__init__(parent, "Login", RENDER_WIDTH//4, RENDER_HEIGHT//4, "Please enter your login credentials.", RENDER_WIDTH//2-RENDER_WIDTH//8, RENDER_HEIGHT//2-RENDER_HEIGHT//8, DEFAULT_FONT)
        username_text = TextField(self, self.rect.w//8, self.rect.h//2, 3*self.rect.w//8, CHAR_HEIGHT[DEFAULT_FONT]*1.3, "Login:", True)
        password_text = TextField(self, 3*DEFAULT_GAP, 3*self.rect.h//4, 3*self.rect.w//8, CHAR_HEIGHT[DEFAULT_FONT]*1.3, "Password:", True)
        self.username_input = InputBox(self, 3*self.rect.w//8, self.rect.h//2, self.rect.w//2)
        self.password_input = InputBoxPassword(self, 3*self.rect.w//8, 3*self.rect.h//4, self.rect.w//2)
        self.add_element(username_text)
        self.add_element(self.username_input)
        self.add_element(password_text)
        self.add_element(self.password_input)
    
    def handle_event(self, event: Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.close()
                if value := self.get_root().control_panel.account_manager.attempt_login(username=self.username_input.text, password=self.password_input.text):
                    self.get_root().terminal.log.print_to_log(f"Logged in as {value.username}", (255,255,0))
                else:
                    self.get_root().terminal.log.print_to_log(f"Could not log in as {self.username_input.text}", (255,0,0))
                return
            if event.key == pg.K_ESCAPE:
                return
        super().handle_event(event)
    

class Button(Widget):
    def __init__(self, parent: 'Widget', x: int, y: int, w: int, h: int, text: str, font: pg.font.Font=DEFAULT_FONT) -> None:
        super().__init__(parent, x, y, w, h)
        self.text = text
        self.font = font
    
    def handle_event(self, event: Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            self.hit_button()
            return
        if event.type == pg.KEYUP:
            if event.key == pg.K_SPACE or event.key == pg.K_RETURN:
                self.hit_button()
                return
        super().handle_event(event)
    
    def hit_button(self):
        self.parent.close()
    
    def render_text(self):
        text_surface = self.font.render(self.text, True, self.color)
        self.surface.blit(text_surface, (0, 0))
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.render_text()
        self.render_border()
        super().blit_from_children()


class TextField(Widget):
    def __init__(self, parent: Widget, x, y, w, h, text: str, transparent: bool = False, load_ascii_file=False, font: pg.font.Font = DEFAULT_FONT) -> None:
        super().__init__(parent, x, y, w, h, None)
        self.transparent = transparent
        if transparent:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0,0,0,0))
        if not load_ascii_file:
            self.text = text
            self.max_chars = self.rect.width // CHAR_WIDTH[font]
            self.lines = break_up_string_into_lines(text, self.max_chars)
        else:
            with open(text, 'r') as file:
                self.lines = [line.rstrip() for line in file]
        self.font = font
    
    def render_text(self):
        y = 0
        for line in self.lines:
            text_surface = self.font.render(line, True, self.color)
            self.surface.blit(text_surface, (DEFAULT_GAP, DEFAULT_GAP + y))
            y += text_surface.get_height()
    
    def render(self):
        if not self.transparent:
            self.surface.fill(BACKGROUND_COLOR)
            self.render_border()
        self.render_text()
        self.blit_from_children()


class Image(Widget):
    def __init__(self, parent: Widget, x, y, w, h, image_path: str) -> None:
        super().__init__(parent, x, y, w, h, None)
        image_surface = pg.image.load(image_path)
        self.surface = pg.transform.scale(image_surface, self.surface.get_size())
    
    def render(self):
        self.render_border()
        self.blit_from_children()


class Video(Widget):
    def __init__(self, parent: Widget, x, y, w, h, video_path: str) -> None:
        super().__init__(parent, x, y, w, h, None)
        self.video = cv2.VideoCapture(video_path)
        self.playing, self.video_image = self.video.read()
        self.paused = False
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
    
    def handle_event(self, event: Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.paused = not self.paused
        return super().handle_event(event)
    
    def render(self):
        if self.playing:
            video_surf = pg.image.frombuffer(self.video_image.tobytes(), self.video_image.shape[1::-1], "BGR")
            video_surf = pg.transform.scale(video_surf, self.surface.get_size())
            self.surface.blit(video_surf, (0, 0))
        self.render_border()
    
    def advance_video(self):
        self.playing, self.video_image = self.video.read()
        if not self.playing:
            return
        self.flag_as_needing_rerender()
    
    def update(self, tick: int, dt: int):
        if not self.playing:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.advance_video()
            self.paused = True
        frame = tick * self.fps // TARGET_FRAME_RATE
        if frame > self.current_frame and not self.paused:
            self.advance_video()
            self.current_frame = frame


class STLRenderer(Widget):
    def __init__(self, parent, stl_path, x, y, w, h) -> None:
        super().__init__(parent, x, y, w, h)
        self.stl_path = stl_path
        self.camera = stlr.Camera(shift=(w//2,h//2))
        self.set_model(stl_path=stl_path)
    
    def set_model(self, stl_path: str):
        self.stl_path = stl_path
        self.unique_edges = stlr.extract_unique_edges(mesh := stlr.read_stl(stl_path))
        min_x, max_x, min_y, max_y, min_z, max_z = stlr.find_mins_maxs(mesh)
        max_bounding_box = max((max_x-min_x), (max_y-min_y), (max_z-min_z))
        self.camera.zoom = 0.9 * min(self.surface.get_width(), self.surface.get_height()) / max_bounding_box
        self.flag_as_needing_rerender()
    
    def handle_event(self, event: Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_d:
                self.set_model("media/roboter.stl")
                self.camera.zoom = self.surface.get_height()
        return super().handle_event(event)
    
    def update(self, tick: int, dt: int):
        degrees_per_second = 45
        if self.active:
            degrees = degrees_per_second*dt/1000
            keys = pg.key.get_pressed()
            if keys[pg.K_LEFT]:
                self.camera.rotate_left_right(-degrees)
            if keys[pg.K_RIGHT]:
                self.camera.rotate_left_right(degrees)
            if keys[pg.K_UP]:
                self.camera.rotate_up_down(degrees)
            if keys[pg.K_DOWN]:
                self.camera.rotate_up_down(-degrees)
            if any((keys[pg.K_LEFT], keys[pg.K_RIGHT], keys[pg.K_UP], keys[pg.K_DOWN])):
                self.flag_as_needing_rerender()
    
    def render_wireframe(self):
        wireframe = stlr.project_to_2d(self.unique_edges, self.camera)
        color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        for line_segment in wireframe:
            pg.draw.line(self.surface, color, line_segment[0], line_segment[1])
    
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.render_wireframe()
        self.render_border()


class InputBox(Widget):
    def __init__(self, parent: 'Widget', x: int, y: int, w: int, h: int = None, font = DEFAULT_FONT) -> None:
        if h is None:
            h = CHAR_HEIGHT[font]*1.3
        super().__init__(parent, x, y, w, h)
        self.color = COLOR_INACTIVE
        self.font = font
        self.text = ''
        self.max_chars = w // CHAR_WIDTH[font]
        self.caret_position = 0
        self.draw_caret = False
        self.selection_range = None
        self.history: list[str] = []
        self.history_index = 0

    def handle_event(self, event: Event):
        if event.type == pg.TEXTINPUT and len(self.text) < self.max_chars:
            if self.selection_range:
                self.erase_selection_range()
            self.text = self.text[0:self.caret_position] + event.text + self.text[self.caret_position:]
            self.caret_position += 1
            self.flag_as_needing_rerender()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text:
                    self.parent.handle_text(self.text)
                    if self.text in self.history:
                        self.history.remove(self.text)
                    self.history.append(self.text)
                self.text = ''
                self.caret_position = 0
                self.selection_range = None
                self.history_index = 0
            elif event.key == pg.K_BACKSPACE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(-1, holding_ctrl=event.mod&pg.KMOD_CTRL, delete=True)
            elif event.key == pg.K_DELETE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(1, holding_ctrl=event.mod&pg.KMOD_CTRL, delete=True)
            elif event.key == pg.K_LEFT:
                self.move_caret(-1, event.mod & pg.KMOD_SHIFT, event.mod & pg.KMOD_CTRL)
            elif event.key == pg.K_RIGHT:
                self.move_caret(1, event.mod & pg.KMOD_SHIFT, event.mod & pg.KMOD_CTRL)
            elif event.key == pg.K_UP:
                if self.history_index > -len(self.history):
                    self.history_index -= 1
                    self.text = self.history[self.history_index]
                self.caret_position = len(self.text)
            elif event.key == pg.K_DOWN:
                if self.history_index < -1:
                    self.history_index += 1
                    self.text = self.history[self.history_index]
                self.caret_position = len(self.text)
            elif event.key == pg.K_a and event.mod & pg.KMOD_CTRL:
                self.selection_range = [0, len(self.text)]
            elif event.key == pg.K_c and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    self.get_root().clipboard = self.text[min(self.selection_range):max(self.selection_range)]
            elif event.key == pg.K_x and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    self.get_root().clipboard = self.text[min(self.selection_range):max(self.selection_range)]
                    self.erase_selection_range()
            elif event.key == pg.K_v and event.mod & pg.KMOD_CTRL:
                if clipboard := self.get_root().clipboard:
                    if self.selection_range:
                        self.erase_selection_range()
                    self.text = self.text[:self.caret_position] + clipboard + self.text[self.caret_position:]
                    self.move_caret(len(clipboard))
            self.flag_as_needing_rerender()
        super().handle_event(event)
    
    def deactivate(self) -> None:
        self.draw_caret = False
        super().deactivate()
    
    def update(self, tick: int, dt: int):
        if self.active:
            self.blink_caret(tick)
    
    def blink_caret(self, tick):
        blinks_per_second = 1
        ticks_per_blink = TARGET_FRAME_RATE / blinks_per_second
        if self.draw_caret == False and tick % ticks_per_blink < ticks_per_blink / 2:
            self.draw_caret = True
            self.flag_as_needing_rerender()
        elif self.draw_caret == True and tick % ticks_per_blink > ticks_per_blink / 2:
            self.draw_caret = False
            self.flag_as_needing_rerender()
    
    def move_caret(self, amount: int, holding_shift: bool = False, holding_ctrl: bool = False, delete=False):
        original_position = self.caret_position
        if holding_ctrl:
            if amount > 0:
                space_index = self.text.find(' ', self.caret_position)
                space_index = space_index if space_index != -1 else len(self.text)
            elif amount < 0:
                space_index = self.text.rfind(' ', 0, max(0, self.caret_position-1))
            amount = space_index - self.caret_position + 1
            
        if not holding_shift and self.selection_range:
            if amount > 0:
                self.caret_position = max(self.selection_range)
            elif amount < 0:
                self.caret_position = min(self.selection_range)
        else:
            self.caret_position += amount
            self.caret_position = min(max(0, self.caret_position), len(self.text))

        if delete:
            self.text = self.text[:min(self.caret_position, original_position)] + self.text[max(self.caret_position,original_position):]
            self.caret_position = min(self.caret_position, original_position)
        if not holding_shift:
            self.selection_range = None
        elif self.selection_range:
            self.selection_range[1] = self.caret_position
        else:
            self.selection_range = [original_position, self.caret_position]
    
    def erase_selection_range(self):
        self.text = self.text[0:min(self.selection_range)] + self.text[max(self.selection_range):]
        self.caret_position = min(self.selection_range)
        self.selection_range = None
    
    def render_text(self):
        text_surface = self.font.render(self.text, True, self.color)
        self.surface.blit(text_surface, (CHAR_WIDTH[self.font]//3, 5))
    
    def render_caret(self):
        x = CHAR_WIDTH[self.font]*(self.caret_position+1/3)
        pg.draw.line(self.surface, self.color, (x, CHAR_HEIGHT[self.font]//6),
                                               (x, self.rect.height - CHAR_HEIGHT[self.font]//6), LINE_THICKNESS_THIN)
    
    def render_selection(self):
        x = int(CHAR_WIDTH[self.font]*(min(self.selection_range)+1/3))
        y = CHAR_HEIGHT[self.font]//8
        w = CHAR_WIDTH[self.font]*(max(self.selection_range)-min(self.selection_range))
        h = self.rect.height - 2*CHAR_HEIGHT[self.font]//8
        pixels = pg.surfarray.pixels3d(self.surface)
        pixels[x:x+w, y:y+h, 1] = 255 - pixels[x:x+w, y:y+h, 1]
        
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.render_text()
        if self.selection_range:
            self.render_selection()
        if self.draw_caret and not self.selection_range:
            self.render_caret()
        self.render_border()
        self.blit_from_children()


class InputBoxPassword(InputBox):
    def __init__(self, parent: Widget, x: int, y: int, w: int, h: int = None, font=DEFAULT_FONT) -> None:
        super().__init__(parent, x, y, w, h, font)
        
    def render_text(self):
        hidden_text = "*" * len(self.text)
        text_surface = self.font.render(hidden_text, True, self.color)
        self.surface.blit(text_surface, (CHAR_WIDTH[self.font]//3, 5))
        

class Log(Widget):
    def __init__(self, parent: 'Widget', x: int, y: int, w: int, h: int, font=DEFAULT_FONT):
        super().__init__(parent, x, y, w, h)
        self.font = font
        self.max_chars = w // CHAR_WIDTH[font]
        self.surface.fill(BACKGROUND_COLOR)
    
    def print_to_log(self, text, color = COLOR_ACTIVE):
        if len(text) > self.max_chars:
            first_half, second_half = break_up_string(text, self.max_chars)
            self.print_to_log(first_half, color)
            self.print_to_log('  ' + second_half.lstrip(), color)
            return
        
        font_render_surface = self.font.render(text, True, color, BACKGROUND_COLOR)
        
        dy = font_render_surface.get_height()
        # for removing (overwriting) the green line, ugly solution:
        pg.draw.line(self.surface, BACKGROUND_COLOR, (0, self.surface.get_height()),
                     (self.surface.get_width(), self.surface.get_height()), 2*LINE_THICKNESS_THICK)
        self.surface.scroll(0, -dy)
        override_rect = pg.Rect(0, self.surface.get_height()-dy, self.surface.get_width(), dy)
        pg.draw.rect(self.surface, BACKGROUND_COLOR, override_rect)
        
        self.surface.blit(font_render_surface, (CHAR_WIDTH[self.font]//3, self.surface.get_height() - dy))
        self.flag_as_needing_rerender()
    
    def render(self):
        self.render_border()
        self.blit_from_children()


class Terminal(Widget):
    def __init__(self, parent: 'Desktop', x: int, y: int, w: int, h: int, font=DEFAULT_FONT) -> None:
        self.log = Log(self, DEFAULT_GAP, DEFAULT_GAP, w-2*DEFAULT_GAP, h-CHAR_HEIGHT[font]*1.3-3*DEFAULT_GAP, font)
        self.input_box = InputBox(self, DEFAULT_GAP, h-DEFAULT_GAP-CHAR_HEIGHT[font]*1.3, w-2*DEFAULT_GAP, CHAR_HEIGHT[font]*1.3)
        super().__init__(parent, x, y, w, h, elements=[self.log, self.input_box])
        self.active_element = self.elements[1]
    
    def handle_text(self, text):
        self.log.print_to_log('> ' + text)
        handle_user_input(self, text)
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.render_border()
        self.blit_from_children()


class Radar(Widget):
    def __init__(self, parent: 'Desktop', png: str, x=0, y=0, w=RENDER_WIDTH, h=RENDER_HEIGHT):
        super().__init__(parent, x, y, w, h)
        self.radar = radar.Radar(w, h, png)
        self.png = png
        self.dt = 0

        self.sweep_surface = pg.Surface((RENDER_WIDTH, RENDER_HEIGHT), pg.SRCALPHA)

    # def handle_event(self, event: Event):
    #     return super().handle_event(event)
        
    def update(self, tick: int, dt: int):
        self.dt = dt
        self.flag_as_needing_rerender()

    def render(self):
        self.radar.render_cross_section(self.surface)
        self.surface.blit(self.sweep_surface, (0, 0))
        self.sweep_surface.fill((0,0,0,0))
        self.radar.render_sweep(self.sweep_surface, self.dt)

        
if __name__ == "__main__":
    from control_panel import ControlPanel
    control_panel = ControlPanel(run_window_manager=True, fullscreen=True, use_shaders=True, maintain_aspect_ratio=True)
    