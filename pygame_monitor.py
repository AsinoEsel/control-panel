import pygame as pg
from video_player import play_video
from utils import *

from setup import *
game_manager = None
window_manager = None
terminal = None


class WindowManager:
    def __init__(self) -> None:
        self.widgets = [Terminal(), ]
        self.windows = [Window(self, "PLEASE LOG IN", SCREEN_WIDTH//4, SCREEN_HEIGHT//4), ]
        self._active_element = self.windows[0]
        self.active_element.activate()
    
    def draw(self, screen):
        for widget in self.widgets:
            widget.draw(screen)
        for window in self.windows:
            window.draw(screen)
    
    def handle_event(self, event: pg.event.Event):
        if self.active_element is None:
            raise Exception("No active element!")
        self.active_element.handle_event(event)
    
    def close_window(self, window: 'Window'):
        self.windows.remove(window)
        if self.active_element is window:
            self.active_element = self.windows[-1] if self.windows else self.widgets[0]
    
    @property
    def active_element(self):
        return self._active_element
    
    @active_element.setter
    def active_element(self, element: 'Widget'):
        if element is self._active_element:
            return
        self._active_element.deactivate
        self._active_element = element
        element.activate()


class Widget:
    def __init__(self) -> None:
        self.active = False
        self.color = COLOR_INACTIVE
    
    def activate(self) -> None:
        self.active = True
        self.color = COLOR_ACTIVE
    
    def deactivate(self) -> None:
        self.active = False
        self.color = COLOR_INACTIVE
    
    def draw(self) -> None:
        pass
    

class Window(Widget):
    def __init__(self, window_manager: 'WindowManager', title: str, w: int, h: int) -> None:
        super().__init__()
        self.window_manager = window_manager
        self.rect = pg.Rect(SCREEN_WIDTH/2 - w/2, SCREEN_HEIGHT/2 - h/2, w, h)
        self.inner_rect = pg.Rect(self.rect.left + DEFAULT_GAP, self.rect.top + CHAR_HEIGHT + DEFAULT_GAP,
                                  self.rect.width - 2*DEFAULT_GAP, self.rect.height - CHAR_HEIGHT - 2*DEFAULT_GAP)
        self.title = title
        self.title_surface = FONT.render(self.title, True, self.color)
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.close()
    
    def activate(self) -> None:
        super().activate()
        self.title_surface = FONT.render(self.title, True, self.color)
    
    def close(self):
        self.window_manager.close_window(self)
    
    def draw(self, screen):
        pg.draw.rect(screen, BACKGROUND_COLOR, self.rect)
        screen.blit(self.title_surface, (self.rect.left + DEFAULT_GAP, self.rect.top + DEFAULT_GAP))
        pg.draw.rect(screen, self.color, self.rect, LINE_THICKNESS_THIN)
        pg.draw.rect(screen, self.color, self.inner_rect, LINE_THICKNESS_THIN)


class Button:
    def __init__(self, parent: 'Widget', text: str) -> None:
        self.parent = parent
        self.text = text
        self.rect = pg.Rect()


class InputBox:
    def __init__(self, parent: 'Widget', x: int, y: int, w: int, h: int) -> None:
        self.parent = parent
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = ''
        self.text_surface = FONT.render(self.text, True, self.color)
        self.max_chars = self.rect.width // CHAR_WIDTH
        self.caret_position = 0

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text:
                    self.parent.handle_text(self.text)
                self.text = ''
                self.caret_position = 0
                self.render_text()
            elif event.key == pg.K_BACKSPACE:
                if self.caret_position > 0:
                    self.text = self.text[0:self.caret_position-1] + self.text[self.caret_position:]
                    self.caret_position -= 1
                    self.render_text()
            elif event.key == pg.K_DELETE:
                if self.caret_position < len(self.text):
                    self.text = self.text[0:self.caret_position] + self.text[self.caret_position+1:]
                    self.render_text()
            elif event.key == pg.K_LEFT:
                if self.caret_position > 0:
                    self.caret_position -= 1
            elif event.key == pg.K_RIGHT:
                if self.caret_position < len(self.text):
                    self.caret_position += 1
            else:
                if not (event.mod & pg.KMOD_CTRL) and is_allowed_character(event.unicode) and len(self.text) < self.max_chars:
                    self.text += event.unicode
                    self.caret_position += 1
                    self.render_text()
    
    def render_text(self):
        self.text_surface = FONT.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.text_surface, (self.rect.x+5, self.rect.y+5))
        x = self.rect.left + self.caret_position*CHAR_WIDTH+CHAR_WIDTH//3
        pg.draw.line(screen, self.color, (x, self.rect.top + CHAR_WIDTH//3), (x, self.rect.bottom - CHAR_WIDTH//3), LINE_THICKNESS_THIN)
        pg.draw.rect(screen, self.color, self.rect, 2)


class Terminal(Widget):
    def __init__(self) -> None:
        super().__init__()
        # self.rect = pg.Rect(0, 0, SCREEN_WIDTH/2, SCREEN_HEIGHT)
        # self.surface = pg.Surface(self.rect)
        self.outline_rect = pg.Rect(DEFAULT_GAP, DEFAULT_GAP, SCREEN_WIDTH/2-2*DEFAULT_GAP, SCREEN_HEIGHT-2*DEFAULT_GAP)
        self.log_surface = pg.Surface((self.outline_rect.width-2*DEFAULT_GAP, self.outline_rect.height-50-2*DEFAULT_GAP))
        self.log_surface.fill(BACKGROUND_COLOR)
        self.input_box = InputBox(self, 2*DEFAULT_GAP, SCREEN_HEIGHT-2*DEFAULT_GAP-CHAR_HEIGHT*1.3, self.outline_rect.width-2*DEFAULT_GAP, CHAR_HEIGHT*1.3)
        self.max_chars = int(self.outline_rect.width / FONT.render("A", False, (0, 0, 0)).get_width())
        # self.log = []
    
    def handle_event(self, event: pg.event.Event):
        self.input_box.handle_event(event)
    
    def handle_text(self, text):
        self.print_to_log('> ' + text)
        match text:
            case "/help":
                self.print_to_log("List of recognized commands:", (255,255,0))
                self.print_to_log("/help       - See this text", (255,255,0))
                self.print_to_log("/play <ID>  - Play a video file", (255,255,0))
            case _ if text.startswith("/play"):
                match text[6:]:
                    case "VHS14":
                        self.print_to_log("Playing VHS14...", (255, 255, 0))
                        play_video("media/video.mov")
                    case _:
                        self.print_to_log(f"Could not find video {text[6:]}")
            case _:
                self.print_to_log(f"{text} is not a recognized command. Try /help for help.", (255, 0, 0))
    
    def print_to_log(self, text, color = COLOR_ACTIVE):
        if len(text) > self.max_chars:
            first_half, second_half = break_up_string(text, self.max_chars)
            self.print_to_log(first_half, color)
            self.print_to_log(' ' + second_half, color)
            return
        
        font_render_surface = FONT.render(text, True, color, BACKGROUND_COLOR)
        
        dy = font_render_surface.get_height()
        self.log_surface.scroll(0, -dy)
        override_rect = pg.Rect(0, self.log_surface.get_height()-dy, self.log_surface.get_width(), dy)
        pg.draw.rect(self.log_surface, BACKGROUND_COLOR, override_rect)
        
        self.log_surface.blit(font_render_surface, (0, self.log_surface.get_height() - dy))
            
    def update(self) -> None:
        pass
    
    def activate(self) -> None:
        self.input_box.color = COLOR_ACTIVE
        return super().activate()

    def deactivate(self) -> None:
        self.input_box.color = COLOR_INACTIVE
        return super().deactivate()
        
    def draw(self, screen) -> None:
        screen.blit(self.log_surface, (self.outline_rect.left+DEFAULT_GAP, self.outline_rect.top+DEFAULT_GAP))
        pg.draw.rect(screen, self.color, self.outline_rect, LINE_THICKNESS_THIN)
        self.input_box.draw(screen)


def run(display_flags=0):
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display_flags)
    clock = pg.time.Clock()
    running = True
    while running:      
        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    running = False
            window_manager.handle_event(event)
        
        # terminal.update()
        
        screen.fill(BACKGROUND_COLOR)
        window_manager.draw(screen)
        for window in window_manager.windows:
            window.draw(screen)
        
        if game_manager.button_is_pressed:
            pg.draw.circle(screen, (255,255,255), (screen.get_width()/2, screen.get_height()/2), 50)
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(60)
        
if __name__ == "__main__":
    from main import GameManager
    game_manager = GameManager()
    window_manager = WindowManager()
    run()