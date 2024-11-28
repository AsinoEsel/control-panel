import pygame as pg
from controlpanel.scripts.gui.window_manager.window_manager_setup import DEBUG_COLOR, COLOR_ACTIVE, COLOR_INACTIVE, ACCENT_COLOR_ACTIVE, ACCENT_COLOR_INACTIVE, LINE_THICKNESS_THIN, RENDER_WIDTH, RENDER_HEIGHT, DEFAULT_GAP, BACKGROUND_COLOR, CHAR_WIDTH, CHAR_HEIGHT, DEFAULT_FONT
from controlpanel.scripts.gui import utils
from controlpanel.scripts.gui.window_manager.event_queue import event_queue, Delay, Event
from typing import Self
from controlpanel.event_manager import EventNameType, EventValueType


class Widget:
    def __init__(self, name: str, parent: Self | None, x=None, y=None, w=None, h=None, elements: list[Self] | None = None, *, do_render_border=True) -> None:
        self.name = name
        if elements is None:
            elements = []
        x = x if x is not None else DEFAULT_GAP 
        y = y if y is not None else DEFAULT_GAP
        w = w if w is not None else parent.surface.get_width()-2*DEFAULT_GAP
        h = h if h is not None else parent.surface.get_height()-2*DEFAULT_GAP
        self.parent: Widget = parent
        self.position = pg.Vector2(x, y)
        self.rect = pg.Rect(0, 0, w, h)
        self.surface = pg.Surface((w, h))
        self.surface.fill(DEBUG_COLOR)
        self.active = False
        self.color = COLOR_INACTIVE
        self.accent_color = ACCENT_COLOR_INACTIVE
        self.elements = elements if elements is not None else []
        self.active_element = elements[0] if elements else None
        self.needs_reblit = True
        self.needs_rerender = True
        self.do_render_border = do_render_border

    def fire_event(self, event_name: EventNameType, event_value: EventValueType = None):
        from controlpanel.scripts import ControlAPI
        ControlAPI.fire_event(self.name, event_name, event_value)
    
    def add_element(self, element: 'Widget', make_active_element: bool = False):
        self.get_desktop().register_widget(element)
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
    
    def get_desktop(self) -> 'Desktop':
        current = self
        while current.parent:
            current = current.parent
        return current

    def update(self, tick: int, dt: float, joysticks: dict[int: pg.joystick.JoystickType]):
        pass
    
    def propagate_update(self, tick: int, dt: float, joysticks: dict[int: pg.joystick.JoystickType]):
        self.update(tick, dt, joysticks)
        for element in self.elements:
            element.propagate_update(tick, dt, joysticks)
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
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            #  print(f"Handling event in {self}: {[element.title for element in self.elements if isinstance(element, Window)]}")
            event.pos = event.pos - self.position
            for element in reversed(self.elements):
                if pg.Rect(element.position, element.rect.size).collidepoint(event.pos):
                    if self.active_element is not None:
                        self.active_element.deactivate()
                    self.active_element = element
                    self.active_element.activate()
                    element.handle_event(event)
                    return
            if self.active_element is not None:
                self.active_element.deactivate()
                self.active_element = None
        if self.active_element is not None:
            self.active_element.handle_event(event)
            return
        if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
            if not self.active_element and self.elements:
                self.active_element = self.elements[0]
                self.active_element.activate()
            elif self.parent:
                self.parent.next_element()
    
    def activate(self) -> None:
        self.fire_event("Activate")

        def blink() -> Event:
            yield from Delay(0.2)
            self.color = COLOR_INACTIVE
            self.accent_color = ACCENT_COLOR_INACTIVE
            self.flag_as_needing_rerender()
            yield from Delay(0.2)
            if self.active:
                self.color = COLOR_ACTIVE
                self.accent_color = ACCENT_COLOR_ACTIVE
                self.flag_as_needing_rerender()

        self.active = True
        self.color = COLOR_ACTIVE
        self.accent_color = ACCENT_COLOR_ACTIVE
        event_queue.append(blink())
        if self.active_element is not None:
            self.active_element.activate()
        self.flag_as_needing_rerender()
    
    def deactivate(self) -> None:
        self.active = False
        self.color = COLOR_INACTIVE
        self.accent_color = ACCENT_COLOR_INACTIVE
        if self.active_element is not None:
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

    def render_body(self):
        self.surface.fill(self.accent_color)
    
    def render_border(self, thickness=LINE_THICKNESS_THIN):
        if not self.do_render_border:
            return
        pg.draw.rect(self.surface, self.color, self.rect, thickness)
    
    def render(self) -> None:
        self.render_body()
        self.render_border()
        self.blit_from_children()


class Desktop(Widget):
    def __init__(self, name: str) -> None:
        super().__init__(name, None, 0, 0, RENDER_WIDTH, RENDER_HEIGHT)
        self.clipboard = ""
        self.widget_manifest: dict[str: Widget] = dict()

    def register_widget(self, widget: Widget):
        if self.widget_manifest.get(widget.name) is not None:
            raise ValueError(f"Widget with name {widget.name} already exists.")  # TODO: Specify desktop name
        self.widget_manifest[widget.name] = widget

    def render_body(self):
        self.surface.fill(BACKGROUND_COLOR)

    def blit_to_parent(self):
        pass
    
    # def add_video_window(self, video_path: str, window_title: str = "Video"):
    #     video_window = Window(self, window_title, w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP)
    #     video = Video(video_window, x=video_window.inner_rect.left, y=video_window.inner_rect.top, w=video_window.inner_rect.w, h=video_window.inner_rect.h,
    #                   video_path=video_path)
    #     video_window.add_element(video)
    #     self.add_element(video_window)
        
        
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

    def handle_event(self, event: pg.event.Event):
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

    def render_body(self):
        self.surface.fill(self.accent_color)
        self.render_title()
        pg.draw.rect(self.surface, BACKGROUND_COLOR, self.inner_rect)
        pg.draw.rect(self.surface, self.color, self.inner_rect, LINE_THICKNESS_THIN)


class TextField(Widget):
    def __init__(self, name: str, parent: Widget, x, y, w, h, text: str, transparent: bool = False, load_ascii_file=False, font: pg.font.Font = DEFAULT_FONT) -> None:
        super().__init__(name, parent, x, y, w, h, None)
        self.transparent = transparent
        if transparent:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0, 0, 0, 0))
        if not load_ascii_file:
            self.text = text
            self.max_chars = self.rect.width // CHAR_WIDTH[font]
            self.lines = utils.break_up_string_into_lines(text, self.max_chars)
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

    def render_body(self):
        self.surface.fill(BACKGROUND_COLOR)
    
    def render(self):
        if not self.transparent:
            self.render_body()
            self.render_border()
        self.render_text()
        self.blit_from_children()
