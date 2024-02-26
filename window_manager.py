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
from shaders import Shaders, SHADER_LIST
from requests.exceptions import ConnectTimeout
import radar


class WindowManager:
    def __init__(self, control_panel, *, fullscreen: bool = False, use_shaders: bool = True):
        self.control_panel: ControlPanel = control_panel
        flags = 0
        if use_shaders:
            flags |= pg.OPENGL | pg.DOUBLEBUF
        if fullscreen:
            flags |= pg.FULLSCREEN
        self.screen = pg.display.set_mode(SCREEN_SIZE, flags=flags)
        self.desktop = Desktop(control_panel)
    
    def run(self, use_shaders: bool):
        pg.init()
        clock = pg.time.Clock()
        tick = 0
        previous_time = time.time()
        
        if use_shaders:
            shaders = Shaders(shaders=SHADER_LIST)
        
        while True:
            tick += 1
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                if RUNNING_ON_LINUX and event.type in (pg.MOUSEMOTION, pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP, pg.MOUSEWHEEL):
                    event.pos = (event.pos[0] * OUTPUT_WIDTH/SCREEN_WIDTH, event.pos[1]*OUTPUT_HEIGHT/SCREEN_HEIGHT)
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
            
            current_time = time.time()
            self.desktop.update(tick, dt=current_time-previous_time)
            previous_time=current_time
            
            if use_shaders:
                shaders.apply(self.desktop.surface)
            else:
                self.screen.blit(self.desktop.surface, (0,0))
                        
            pg.event.pump()
            pg.display.flip()
            clock.tick(TARGET_FRAME_RATE)


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
    
    def update(self, tick: int, dt: float):
        for element in self.elements:
            element.update(tick, dt)
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
        super().__init__(None, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.terminal = Terminal(self, x=DEFAULT_GAP, y=DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT-2*DEFAULT_GAP)
        log = Log(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP)
        empty_widget = Widget(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP)
        image = Image(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP,
                      image_path=os.path.join('media', 'robot36.png'))
        text_field = TextField(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP,
                               text=os.path.join('media','roboter_ascii.txt'), load_ascii_file=True, transparent=False, font=SMALL_FONT)
        stl_renderer = STLRenderer(self, "media/fox_centered.stl", x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP,
                                   w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP)
        radar = Radar(self, png='media/red_dot_image.png')
        # self.add_element(self.terminal)
        # self.add_element(log)
        log.print_to_log("STORAGE/VIDEOS/VHS:", (255, 255, 0))
        log.print_to_log("VHS1: MISSING DATA", (255, 0, 0))
        log.print_to_log("VHS2: □□□□□□□ □□□□", (255, 0, 0))
        log.print_to_log("VHS4: DATA CORRUPTED", (255, 0, 0))
        log.print_to_log("VHS9: DATA CORRUPTED", (255, 0, 0))
        log.print_to_log("VHS10: MISSING DATA", (255, 0, 0))
        log.print_to_log("VHS14: READY", (0, 255, 0))
        log.print_to_log("VHS17: DELETED", (255, 0, 0))
        log.print_to_log("VHS18: MISSING DATA", (255, 0, 0))
        #self.add_element(radar)
        self.add_element(empty_widget)
        #empty_widget.add_element(Window(empty_widget, "cooltitle", 300, 100, "cooltext", 80, 120))
        #empty_widget.add_element(Window(empty_widget, "coolertitle", 400, 100, "coolertext"))
        #empty_widget.add_element(Window(empty_widget, "coolesttitle", 300, 150, "this text is so cool you wouldn't believe it"), True)
        self.add_element(LoginWindow(self))
        """window = Window(self, "PLEASE LOG IN", SCREEN_WIDTH//4, SCREEN_HEIGHT//4, "Please enter your login credentials.")
        window.add_element(Button(window, window.rect.w//4, window.rect.h//2, window.rect.w//2, 50, "Close"))
        window.add_element(Button(window, window.rect.w//4, 3*window.rect.h//4, window.rect.w//2, 50, "DOG"))
        self.add_element(window, True)"""
        
        self.clipboard = ""
        
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.blit_from_children()
    
    def blit_to_parent(self):
        pass
    
    def add_video_window(self, video_path: str, window_title: str = "Video"):
        video_window = Window(self, window_title, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP)
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
        super().__init__(parent, "Login", SCREEN_WIDTH//4, SCREEN_HEIGHT//4, "Please enter your login credentials.", SCREEN_WIDTH//2-SCREEN_WIDTH//8, SCREEN_HEIGHT//2-SCREEN_HEIGHT//8, DEFAULT_FONT)
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
    
    def update(self, tick: int, dt: float):
        if not self.playing:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.advance_video()
            self.paused = True
        frame = tick * self.fps // TARGET_FRAME_RATE
        if frame > self.current_frame and not self.paused:
            self.advance_video()
            self.current_frame = frame
        super().update(tick, dt)

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
    
    def update(self, tick: int, dt: float):
        degrees_per_second = 45
        if self.active:
            degrees = degrees_per_second*dt
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
        super().update(tick, dt)
    
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
                    self.text = self.text[:self.caret_position] + clipboard + self.text[self.caret_position:]
                    self.move_caret(len(clipboard))
            self.flag_as_needing_rerender()
        super().handle_event(event)
    
    def deactivate(self) -> None:
        self.draw_caret = False
        super().deactivate()
    
    def update(self, tick: int, dt: float):
        if self.active:
            self.blink_caret(tick)
        super().update(tick, dt)
    
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
    def __init__(self, parent: 'Desktop', png):
        super().__init__(parent, x = 0, y = 0, w = SCREEN_WIDTH, h = SCREEN_HEIGHT)
        self.png = png
        self.flag_as_needing_rerender()

    # def handle_event(self, event: Event):
    #     return super().handle_event(event)
        
    def update(self, tick, dt):
        super().update(tick, dt)
        self.flag_as_needing_rerender()

    def render(self):
        radar.render(self.surface)

        
if __name__ == "__main__":
    from control_panel import ControlPanel
    control_panel = ControlPanel(run_window_manager=True, fullscreen=False, use_shaders=True)
    