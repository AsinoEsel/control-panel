import pygame as pg
from video_player import play_video
from utils import *

from setup import *
game_manager = None
terminal = None


class Window:
    def __init__(self, terminal: 'Terminal', title: str, w: int, h: int) -> None:
        self.terminal = terminal
        self.rect = pg.Rect(SCREEN_WIDTH/2 - w/2, SCREEN_HEIGHT/2 - h/2, w, h)
        self.color = COLOR_ACTIVE
        self.title = title
    
    def handle_event(self, event: pg.event.Event):
        pass
    
    def draw(self, screen):
        pg.draw.rect(screen, BACKGROUD_COLOR, self.rect)
        pg.draw.rect(screen, self.color, self.rect, LINE_THICKNESS_THICK)

class InputBox:
    def __init__(self, terminal: 'Terminal', x: int, y: int, w: int, h: int) -> None:
        self.terminal = terminal
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_ACTIVE
        self.text = ''
        self.txt_surface = FONT.render(self.text, True, self.color)
        self.active = True
        self.max_chars = int(self.rect.width / FONT.render("A", False, (0, 0, 0)).get_width())

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    if self.text:
                        self.terminal.handle_text(self.text)
                    self.text = ''
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if not (event.mod & pg.KMOD_CTRL) and is_allowed_character(event.unicode) and len(self.text) < self.max_chars:
                        self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pg.draw.rect(screen, self.color, self.rect, 2)


class Terminal:
    def __init__(self) -> None:
        self.color = COLOR_ACTIVE
        self.rect = pg.Rect(DEFAULT_GAP, DEFAULT_GAP, SCREEN_WIDTH/2-2*DEFAULT_GAP, SCREEN_HEIGHT-2*DEFAULT_GAP)
        self.log_surface = pg.Surface((self.rect.width-2*DEFAULT_GAP, self.rect.height-50-2*DEFAULT_GAP))
        self.log_surface.fill(BACKGROUD_COLOR)
        self.input_box = InputBox(self, 2*DEFAULT_GAP, SCREEN_HEIGHT-2*DEFAULT_GAP-50, self.rect.width-2*DEFAULT_GAP, 50)
        self.max_chars = int(self.rect.width / FONT.render("A", False, (0, 0, 0)).get_width())
        # self.log = []
    
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
        
        font_render_surface = FONT.render(text, True, color, BACKGROUD_COLOR)
        
        dy = font_render_surface.get_height()
        self.log_surface.scroll(0, -dy)
        override_rect = pg.Rect(0, self.log_surface.get_height()-dy, self.log_surface.get_width(), dy)
        pg.draw.rect(self.log_surface, BACKGROUD_COLOR, override_rect)
        
        self.log_surface.blit(font_render_surface, (0, self.log_surface.get_height() - dy))
            
    def update(self) -> None:
        pass
        
    def draw(self, screen) -> None:
        screen.blit(self.log_surface, (self.rect.left+DEFAULT_GAP, self.rect.top+DEFAULT_GAP))
        pg.draw.rect(screen, self.color, self.rect, LINE_THICKNESS_THIN)
        self.input_box.draw(screen)


def run():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pg.time.Clock()
    running = True
    while running:      
        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    running = False
                case pg.KEYDOWN:
                    match event.key:
                        case pg.K_ESCAPE:
                            running = False
            terminal.input_box.handle_event(event)
        
        # terminal.update()
        
        screen.fill(BACKGROUD_COLOR)
        terminal.draw(screen)
        for window in windows:
            window.draw(screen)
        
        if game_manager.button_is_pressed:
            pg.draw.circle(screen, (255,255,255), (screen.get_width()/2, screen.get_height()/2), 50)
        
        pg.event.pump()
        pg.display.flip()
        clock.tick(60)
        
if __name__ == "__main__":
    from main import GameManager
    game_manager = GameManager()
    terminal = Terminal()
    windows = [Window(terminal, "PLEASE LOG IN", 200, 100), ]
    run()