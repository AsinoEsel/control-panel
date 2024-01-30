import pygame as pg
from video_player import play_video
from utils import *
from setup import *
game_manager = None
terminal = None


class WindowManager:
    def __init__(self, w: int = SCREEN_WIDTH, h: int = SCREEN_HEIGHT) -> None:
        self.surface = pg.Surface((w, h))
        self.surface.fill(BACKGROUND_COLOR)
        self.parent = None
        self.widgets = [Terminal(self, x=DEFAULT_GAP, y=DEFAULT_GAP, w=SCREEN_WIDTH/2-2*DEFAULT_GAP, h=SCREEN_HEIGHT-2*DEFAULT_GAP),
                        Log(self, x=SCREEN_WIDTH/2+DEFAULT_GAP, y=DEFAULT_GAP, w=SCREEN_WIDTH/2-2*DEFAULT_GAP, h=SCREEN_HEIGHT/2-2*DEFAULT_GAP),]
        self.widgets[1].print_to_log("STORAGE/VHS:", (255, 255, 0))
        self.widgets[1].print_to_log("VHS1: MISSING DATA", (255, 0, 0))
        self.widgets[1].print_to_log("VHS2: □□□□□□□ □□□□", (255, 0, 0))
        self.widgets[1].print_to_log("VHS4: DATA CORRUPTED", (255, 0, 0))
        self.widgets[1].print_to_log("VHS9: DATA CORRUPTED", (255, 0, 0))
        self.widgets[1].print_to_log("VHS10: MISSING DATA", (255, 0, 0))
        self.widgets[1].print_to_log("VHS14: READY", (0, 255, 0))
        self.widgets[1].print_to_log("VHS17: DELETED", (255, 0, 0))
        self.widgets[1].print_to_log("VHS18: MISSING DATA", (255, 0, 0))
        self.windows = [Window(self, "PLEASE LOG IN", SCREEN_WIDTH//4, SCREEN_HEIGHT//4), ]
        self.elements = self.widgets + self.windows
        self.active_element = self.windows[0]
        self.active_element.activate()
        self.needs_updating = False
        print(f"Active element at {self.active_element}")
    
    def smart_update(self):
        for element in self.elements:
            element.smart_update()
    
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        for element in self.elements:
            element.blit_to_parent()
    
    def draw(self, screen):
        screen.blit(self.surface, (0,0))
    
    def handle_event(self, event: pg.event.Event):
        if self.active_element is None:
            raise Exception("No active element!")
        self.active_element.handle_event(event)
        
    def close_window(self, window: 'Window'):
        self.windows.remove(window)
        self.elements.remove(window)
        if self.active_element is window:
            self.active_element = self.windows[-1] if self.windows else self.widgets[0]
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


class Widget:
    def __init__(self, parent: 'Widget', x, y, w, h, elements: list['Widget']|None = None) -> None:
        if elements is None:
            elements = []
        self.parent = parent
        self.position = (x, y)
        self.rect = pg.Rect(0, 0, w, h)
        self.surface = pg.Surface((w, h))
        self.surface.fill(DEBUG_COLOR)
        self.active = False
        self.color = COLOR_INACTIVE
        self.accent_color = ACCENT_COLOR_INACTIVE
        self.elements = elements
        self.active_element = elements[0] if elements else None
        self.needs_updating = True
    
    @property
    def window_manager(self):
        current_parent = self.parent
        while not isinstance(current_parent, WindowManager):
            current_parent = current_parent.parent
        return current_parent
    
    def update(self):
        if self.parent is not None:
            self.render()
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
        if self.active_element:
            self.active_element.handle_event(event)
        elif event.type == pg.KEYDOWN and event.key == pg.K_TAB:
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
    
    def render(self) -> None:
        self.surface.fill(self.accent_color)
        for element in self.elements:
            element.blit_to_parent()
        pg.draw.rect(self.surface, self.color, self.rect, LINE_THICKNESS_THIN)
            

class Window(Widget):
    def __init__(self, parent, title: str, w: int, h: int, font=DEFAULT_FONT) -> None:
        super().__init__(parent, SCREEN_WIDTH/2 - w/2, SCREEN_HEIGHT/2 - h/2, w, h)
        self.inner_rect = pg.Rect(DEFAULT_GAP, CHAR_HEIGHT[font] + DEFAULT_GAP,
                                  w - 2*DEFAULT_GAP, h - CHAR_HEIGHT[font] - 2*DEFAULT_GAP)
        self.font = font
        self.title = title
        self.title_surface = font.render(self.title, True, self.color)
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.close()
        super().handle_event(event)
    
    def activate(self) -> None:
        super().activate()
        # self.title_surface = self.font.render(self.title, True, self.color)
    
    def close(self):
        self.parent.close_window(self)
    
    def render(self):
        self.surface.fill(self.accent_color)
        self.surface.blit(self.title_surface, (DEFAULT_GAP, DEFAULT_GAP))
        pg.draw.rect(self.surface, self.color, self.rect, LINE_THICKNESS_THIN)
        pg.draw.rect(self.surface, ACCENT_COLOR_INACTIVE, self.inner_rect)
        pg.draw.rect(self.surface, self.color, self.inner_rect, LINE_THICKNESS_THIN)
    

class Button(Widget):
    def __init__(self, parent: 'Widget', text: str, x: int, y: int, w: int, h: int) -> None:
        super().__init__(parent, x, y, w, h)
        self.text = text
        self.rect = pg.Rect()


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
        pg.draw.rect(self.surface, self.color, self.rect, 2)  # draw border


class Log(Widget):
    def __init__(self, parent: 'Widget', x: int, y: int, w: int, h: int, font=DEFAULT_FONT):
        super().__init__(parent, x, y, w, h)
        self.font = font
        self.max_chars = int(w / CHAR_WIDTH[font])
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
    
    def render_border(self):
        pg.draw.rect(self.surface, self.color, self.rect, LINE_THICKNESS_THIN)
    
    def render(self):
        self.render_border()


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


def run(display_flags=0):
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display_flags)
    window_manager = WindowManager()
    from debug_util import find_all_children
    clock = pg.time.Clock()
    running = True
    tick = 0
    while running:
        tick += 1
        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    running = False
            window_manager.handle_event(event)
            
        window_manager.smart_update()
        # count_children_needs_updating()
        window_manager.render()
        window_manager.draw(screen)
        
        if game_manager.button_is_pressed:
            pg.draw.circle(screen, (255,255,255), (screen.get_width()/2, screen.get_height()/2), 50)
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(30)
        
if __name__ == "__main__":
    from main import GameManager
    game_manager = GameManager()
    run()