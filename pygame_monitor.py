import pygame as pg
import os
from pygame.event import Event
from video_player import play_video
from utils import *
from setup import *
import debug_util
game_manager = None
terminal = None


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
        self.needs_updating = True
    
    def get_root(self):
        current = self
        while current.parent:
            current = self.parent
        return current
    
    def update(self):
        self.render()
        if self.parent:
            self.blit_to_parent()
        self.needs_updating = False

    def smart_update(self):
        if not self.needs_updating:
            return
        for element in self.elements:
            element.smart_update()
        self.update()
    
    def next_element(self):
        self.active_element.deactivate()
        index = self.elements.index(self.active_element)
        index += 1
        if index >= len(self.elements):
            self.active_element = self.elements[0]
            self.parent.next_element()
        else:
            self.active_element = self.elements[index]
            self.active_element.activate()
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            event.pos = (event.pos[0] - self.position[0], event.pos[1] - self.position[1])
            for element in reversed(self.elements):
                if pg.Rect(element.position, element.rect.size).collidepoint(event.pos):
                    if not self.active_element:
                        return
                    self.active_element.deactivate()
                    self.active_element = element
                    self.active_element.activate()
                    element.handle_event(event)
                    return
            return
        if self.active_element:
            self.active_element.handle_event(event)
            return
        if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
            self.parent.next_element()
    
    def activate(self) -> None:
        self.active = True
        self.color = COLOR_ACTIVE
        self.accent_color = ACCENT_COLOR_ACTIVE
        if self.active_element:
            self.active_element.activate()
        self.flag_as_needs_updating()
    
    def deactivate(self) -> None:
        self.active = False
        self.color = COLOR_INACTIVE
        self.accent_color = ACCENT_COLOR_INACTIVE
        if self.active_element:
            self.active_element.deactivate()
        self.flag_as_needs_updating()
    
    def flag_as_needs_updating(self):
        # Mark this node and all its ancestors for update
        node = self
        while node:
            node.needs_updating = True
            node = node.parent
    
    def blit_to_parent(self):
        self.parent.surface.blit(self.surface, self.position)
    
    def blit_from_children(self):
        for element in self.elements:
            element.blit_to_parent()
    
    def render_border(self, thickness=LINE_THICKNESS_THIN):
        pg.draw.rect(self.surface, self.color, self.rect, thickness)
    
    def render(self) -> None:
        self.surface.fill(self.accent_color)
        pg.draw.rect(self.surface, self.color, self.rect, LINE_THICKNESS_THIN)
        self.blit_from_children()


class WindowManager(Widget):
    def __init__(self) -> None:
        terminal = Terminal(self, x=DEFAULT_GAP, y=DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT-2*DEFAULT_GAP)
        log = Log(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP)
        empty_widget = Widget(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP)
        image = Image(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP,
                      image_path=os.path.join('media', 'robot36.png'))
        text_field = TextField(self, x=SCREEN_WIDTH//2+DEFAULT_GAP, y=SCREEN_HEIGHT//2+DEFAULT_GAP, w=SCREEN_WIDTH//2-2*DEFAULT_GAP, h=SCREEN_HEIGHT//2-2*DEFAULT_GAP,
                               text=os.path.join('media','roboter_ascii.txt'), load_ascii_file=True, transparent=False, font=SMALL_FONT)
        super().__init__(None, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, [terminal, log, empty_widget])
        # self.surface.fill(BACKGROUND_COLOR)
        log.print_to_log("STORAGE/VHS:", (255, 255, 0))
        log.print_to_log("VHS1: MISSING DATA", (255, 0, 0))
        log.print_to_log("VHS2: □□□□□□□ □□□□", (255, 0, 0))
        log.print_to_log("VHS4: DATA CORRUPTED", (255, 0, 0))
        log.print_to_log("VHS9: DATA CORRUPTED", (255, 0, 0))
        log.print_to_log("VHS10: MISSING DATA", (255, 0, 0))
        log.print_to_log("VHS14: READY", (0, 255, 0))
        log.print_to_log("VHS17: DELETED", (255, 0, 0))
        log.print_to_log("VHS18: MISSING DATA", (255, 0, 0))
        empty_widget.elements.append(Window(empty_widget, "cooltitle", 300, 100, "cooltext"))
        empty_widget.elements.append(Window(empty_widget, "coolertitle", 400, 100, "coolertext"))
        empty_widget.elements.append(Window(empty_widget, "coolesttitle", 300, 150, "this text is so cool you wouldn't believe it"))
        empty_widget.active_element = empty_widget.elements[0]
        window = Window(self, "PLEASE LOG IN", SCREEN_WIDTH//4, SCREEN_HEIGHT//4, "Please enter your login credentials.")
        window.elements.append(Button(window, window.rect.w//4, window.rect.h//2, window.rect.w//2, 50, "Close"))
        window.elements.append(Button(window, window.rect.w//4, 3*window.rect.h//4, window.rect.w//2, 50, "DOG"))
        self.elements.append(window)
        window.active_element = window.elements[0]
        # self.active_element.activate()
            
    """def smart_update(self):
        for element in self.elements:
            element.smart_update()"""
    
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.blit_from_children()
    
    def draw(self, screen):
        screen.blit(self.surface, (0,0))
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            for element in reversed(self.elements):
                if pg.Rect(element.position, element.rect.size).collidepoint(event.pos):
                    self.active_element.deactivate()
                    self.active_element = element
                    self.active_element.activate()
                    element.handle_event(event)
                    break
            return
        self.active_element.handle_event(event)
        
    def close_window(self, window: 'Window'):
        self.elements.remove(window)
        if self.active_element is window:
            self.active_element = self.elements[0]
            self.active_element.activate()
        self.needs_updating = True
    
    def next_element(self):
        self.active_element.deactivate()
        index = self.elements.index(self.active_element)
        index += 1
        if index >= len(self.elements):
            index = 0
        self.active_element = self.elements[index]
        self.active_element.activate()
            

class Window(Widget):
    def __init__(self, parent, title: str, w: int, h: int, text: str|None = None, x: int|None = None, y: int|None = None, font=DEFAULT_FONT) -> None:
        x = parent.surface.get_width()//2 - w//2 if x is None else x
        y = parent.surface.get_height()//2 - h//2 if y is None else y
        super().__init__(parent, x, y, w, h)
        self.inner_rect = pg.Rect(DEFAULT_GAP, CHAR_HEIGHT[font] + DEFAULT_GAP,
                                  w - 2*DEFAULT_GAP, h - CHAR_HEIGHT[font] - 2*DEFAULT_GAP)
        self.font = font
        self.title = title
        if text:
            self.elements.append(TextField(self, self.inner_rect.left + DEFAULT_GAP, self.inner_rect.top + DEFAULT_GAP, 
                                           self.inner_rect.width - 2*DEFAULT_GAP, self.inner_rect.height//2, text, True))

    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEMOTION:
            if event.buttons[0]:
                self.position += pg.Vector2(event.rel)
                self.position.x = max(0, self.position.x)
                self.position.x = min(self.parent.surface.get_width()-self.rect.w, self.position.x)
                self.position.y = max(0, self.position.y)
                self.position.y = min(self.parent.surface.get_height()-self.rect.h, self.position.y)
                self.parent.flag_as_needs_updating()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.close()
        super().handle_event(event)
    
    def activate(self):
        super().activate()
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


class InputBox(Widget):
    def __init__(self, parent: 'Widget', x: int, y: int, w: int, h: int, font = DEFAULT_FONT) -> None:
        super().__init__(parent, x, y, w, h)
        self.color = COLOR_INACTIVE
        self.font = font
        self.text = ''
        self.max_chars = w // CHAR_WIDTH[font]
        self.caret_position = 0

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.TEXTINPUT and len(self.text) < self.max_chars:
            self.text = self.text[0:self.caret_position] + event.text + self.text[self.caret_position:]
            self.caret_position += 1
            self.flag_as_needs_updating()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text:
                    self.parent.handle_text(self.text)
                self.text = ''
                self.caret_position = 0
            elif event.key == pg.K_BACKSPACE:
                if self.caret_position > 0:
                    self.text = self.text[0:self.caret_position-1] + self.text[self.caret_position:]
                    self.caret_position -= 1
            elif event.key == pg.K_DELETE:
                if self.caret_position < len(self.text):
                    self.text = self.text[0:self.caret_position] + self.text[self.caret_position+1:]
            elif event.key == pg.K_LEFT:
                if self.caret_position > 0:
                    self.caret_position -= 1
            elif event.key == pg.K_RIGHT:
                if self.caret_position < len(self.text):
                    self.caret_position += 1
            """else:
                if not (event.mod & pg.KMOD_CTRL) and is_allowed_character(event.unicode) and len(self.text) < self.max_chars:
                    self.text = self.text[0:self.caret_position] + event.unicode + self.text[self.caret_position:]
                    self.caret_position += 1"""
            self.flag_as_needs_updating()
        super().handle_event(event)
    
    def render_text(self):
        text_surface = self.font.render(self.text, True, self.color)
        self.surface.blit(text_surface, (CHAR_WIDTH[self.font]//3, 5))
    
    def render_caret(self):
        x = CHAR_WIDTH[self.font]*(self.caret_position+1/3)
        pg.draw.line(self.surface, self.color, (x, CHAR_HEIGHT[self.font]//4),
                                               (x, self.rect.height - CHAR_HEIGHT[self.font]//4), LINE_THICKNESS_THIN)
    
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.render_text()
        self.render_caret()
        self.render_border()
        self.blit_from_children()


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
        self.flag_as_needs_updating()
    
    def render(self):
        self.render_border()
        self.blit_from_children()


class Terminal(Widget):
    def __init__(self, parent: 'WindowManager', x: int, y: int, w: int, h: int, font=DEFAULT_FONT) -> None:
        self.log = Log(self, DEFAULT_GAP, DEFAULT_GAP, w-2*DEFAULT_GAP, h-CHAR_HEIGHT[font]*1.3-3*DEFAULT_GAP, font)
        self.input_box = InputBox(self, DEFAULT_GAP, h-DEFAULT_GAP-CHAR_HEIGHT[font]*1.3, w-2*DEFAULT_GAP, CHAR_HEIGHT[font]*1.3)
        super().__init__(parent, x, y, w, h, elements=[self.log, self.input_box])
        self.active_element = self.elements[1]
    
    def handle_text(self, text):
        self.log.print_to_log('> ' + text)
        match text:
            case "/help":
                self.log.print_to_log("List of recognized commands:", (255,255,0))
                self.log.print_to_log("/help       - See this text", (255,255,0))
                self.log.print_to_log("/play <ID>  - Play a video file", (255,255,0))
            case _ if text.startswith("/play"):
                match text[6:]:
                    case "VHS14" | "14":
                        self.log.print_to_log("Playing VHS14...", (255, 255, 0))
                        play_video("media/video.mov")
                    case _:
                        self.log.print_to_log(f"Could not find video {text[6:]}", (255, 255, 0))
            case _:
                self.log.print_to_log(f"{text} is not a recognized command. Try /help for help.", (255, 0, 0))
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.render_border()
        self.blit_from_children()


def run(display_flags=0):
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display_flags)
    window_manager = WindowManager()
    window_manager.surface = screen
    clock = pg.time.Clock()
    running = True
    while running:
        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    running = False
            window_manager.handle_event(event)
        
        window_manager.smart_update()
        
        if game_manager.button_is_pressed:
            pg.draw.circle(screen, (255,255,255), (screen.get_width()/2, screen.get_height()/2), 50)
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(60)
        
if __name__ == "__main__":
    from main import GameManager
    game_manager = GameManager()
    run()