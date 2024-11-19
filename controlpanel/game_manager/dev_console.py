import pygame as pg
import os
import inspect
from typing import get_type_hints, TYPE_CHECKING, Callable, Any
from itertools import islice
import types
import sys
if TYPE_CHECKING:
    from controlpanel.game_manager import GameManager


ColorType = tuple[int, int, int]


class OutputRedirector:
    stdout = sys.stdout

    def __init__(self, func):
        self.func = func

    def write(self, text):
        self.stdout.write(text)
        if text.strip():  # Ignore empty lines
            self.func(text, mirror_to_stdout=False)

    def flush(self):
        self.stdout.flush()


class DeveloperConsole:
    DEFAULT_HEIGHT = 200

    def __init__(self,
                 game_manager: "GameManager",
                 screen_surface: pg.Surface,
                 *,
                 font_name: str = os.path.join(os.path.dirname(__file__), "..", "scripts", "gui", "media", "clacon2.ttf"),
                 font_size: int = 20):
        self.font = pg.font.Font(font_name, font_size)
        self.game_manager = game_manager
        self.open: bool = False
        self.dark_surface = pg.Surface(screen_surface.get_size())
        self.dark_surface.fill((100, 100, 100))

        self.primary_color = (100, 168, 100)
        self.secondary_color = (32, 48, 32)
        self.error_color = (255, 64, 64)
        self.text_color = (200, 200, 200)

        self.char_width = self.font.render("A", False, (255, 255, 255)).get_width()
        self.char_height = self.font.render("A", False, (255, 255, 255)).get_height()
        self.border_thickness = 2

        self.surface = pg.Surface((screen_surface.get_width(), self.DEFAULT_HEIGHT))

        input_box_height = int(self.char_height * 1.5)
        log_width = input_box_width = screen_surface.get_width() - 2 * self.border_thickness
        max_log_height = self.game_manager.screen.get_height() - input_box_height - 3 * self.border_thickness

        self.input_box = InputBox(self, (input_box_width, input_box_height))
        self.log = Log(self, (log_width, max_log_height))

        sys.stdout = OutputRedirector(self.log.print)

    def handle_command(self, command: str):
        self.log.print(">>> " + command, color=self.text_color)
        func_name, *args = command.split()
        func = self.game_manager.current_game.get_methods().get(func_name)
        if func_name == "help":
            if not args:
                self.log.print("List of all available commands: (type help <command> for help)")
                all_methods = self.game_manager.current_game.get_methods().keys()
                column_gap = 2
                column_width = max(len(method_name) for method_name in all_methods) + column_gap
                column_count = self.input_box.max_chars//column_width
                method_iterator = iter(all_methods)
                while True:
                    chunk = list(islice(method_iterator, column_count))
                    if not chunk:
                        break
                    self.log.print("".join(f"{method_name:<{column_width}}" for method_name in chunk), color=self.text_color)
            elif (target_func := self.game_manager.current_game.get_methods().get(args[0])) is not None:
                if target_func.__doc__:
                    self.log.print(target_func.__doc__.strip())
                self.print_usage_string(target_func)
            else:
                self.log.print(f"No method {args[0]} exists in the game {self.game_manager.current_game.__class__.__name__}.", color=self.error_color)
            return
        elif func_name == "exit" or func_name == "quit":
            pg.quit()
        elif func is None:
            self.log.print(f"No method {func_name} exists in the game {self.game_manager.current_game.__class__.__name__}.", color=self.error_color)
            return
        try:
            cast_args = []
            for arg, (param_name, param) in zip(args, inspect.signature(func).parameters.items()):
                param_type = get_type_hints(func).get(param_name, "undef")
                if param_type == "undef":
                    cast_args.append(arg)
                elif type(param_type) is types.UnionType:
                    cast_arg = arg
                    for unioned_type in sorted(param_type.__args__, key=lambda t: t is str):
                        try:
                            cast_arg = unioned_type(arg)
                        except ValueError:
                            continue
                        break
                    cast_args.append(cast_arg)
                else:
                    try:
                        cast_args.append(param_type(arg))
                    except ValueError as e:
                        self.log.print(f"{e.__class__.__name__}: {str(e)}", color=self.error_color)
            result = func(*cast_args)
            self.log.print(str(result))
        except TypeError as e:
            self.log.print(f"{e.__class__.__name__}: {str(e)}", color=self.error_color)
            self.print_usage_string(func)
            return

    def print_usage_string(self, func: Callable[..., Any]):
        string = f"Usage: {func.__name__} "
        for param_name, param in inspect.signature(func).parameters.items():
            param_type = get_type_hints(func).get(param_name, "undef")

            if param_type == "undef":
                param_type_name = "undef"
            elif hasattr(param_type, "__name__"):
                param_type_name = param_type.__name__
            else:
                param_type_name = str(param_type).replace(" ", "")

            param_default = param.default if param.default is not inspect.Parameter.empty else None
            if type(param_default) is str:
                param_default = "'" + param_default + "'"
            string += f"<{param_type_name} {param_name}{"=" + str(param_default) if param_default else ""}> "
        return_type = get_type_hints(func).get('return', "undef")
        return_type_name = return_type.__name__ if return_type != "undef" else "undef"
        string += f"-> {return_type_name}"
        self.log.print(string)

    def resize(self, new_height: int = 100):
        new_height = min(self.game_manager.screen.get_height(), max(self.input_box.surface.get_height() + 2*self.border_thickness, new_height))
        self.surface = pg.Surface((self.surface.get_width(), new_height))

    def handle_events(self, events: list[pg.event.Event]):
        for event in events:
            if event.type == pg.KEYDOWN and (event.key == 1073741921 or event.key == pg.K_PAGEUP):
                self.resize(self.surface.get_height() - 50)
            elif event.type == pg.KEYDOWN and (event.key == 1073741915 or event.key == pg.K_PAGEDOWN):
                self.resize(self.surface.get_height() + 50)
            elif event.type == pg.KEYDOWN and event.key == pg.K_r:
                self.log.render()
            elif event.type == pg.MOUSEWHEEL:
                self.log.history_index -= event.y
                self.log.history_index = max(0, min(self.log.history_index, len(self.log.history)-1))
                self.log.render()
            else:
                self.input_box.handle_event(event)

    def render(self, surface: pg.Surface):
        self.surface.fill(self.primary_color)

        visible_log_height = self.surface.get_height() - self.input_box.surface.get_height() - 3 * self.border_thickness
        self.surface.blit(self.log.surface, (2, 2),
                          (0, self.log.surface.get_height() - visible_log_height, self.log.surface.get_width(), visible_log_height))

        self.input_box.render_body()
        self.surface.blit(self.input_box.surface, (2, self.surface.get_height() - self.input_box.surface.get_height() - self.border_thickness))

        surface.blit(self.dark_surface, (0, 0), special_flags=pg.BLEND_RGB_MULT)
        surface.blit(self.surface, (0, 0))


class Log:
    def __init__(self, dev_console: DeveloperConsole, size: tuple[int, int]):
        self.dev_console = dev_console
        self.surface = pg.Surface(size)
        self.surface.fill(dev_console.secondary_color)

        self.history: list[tuple[str, ColorType]] = []
        self.history_index: int = 0

    def render(self):
        self.surface.fill(self.dev_console.secondary_color)
        for line, color in reversed(self.history[self.history_index::-1]):
            self.print(line, color, mirror_to_stdout=False, append_to_history=False)

    def print(self, string: str, color: ColorType | None = None, *, mirror_to_stdout: bool = True, append_to_history: bool = True):
        if append_to_history:
            self.history.append((string, color))
            self.history_index = len(self.history)
        if mirror_to_stdout:
            print("DEV: " + string, file=sys.__stdout__)
        color = color if color is not None else self.dev_console.primary_color
        font_surface = self.dev_console.font.render(string, True, color, self.dev_console.secondary_color)
        dy = -font_surface.get_height()
        self.surface.scroll(0, dy)
        self.surface.fill(self.dev_console.secondary_color, (0, self.surface.get_height() + dy, self.surface.get_width(), -dy))
        self.surface.blit(font_surface, (0, self.surface.get_height() - font_surface.get_height()))


class InputBox:
    def __init__(self, dev_console: DeveloperConsole, size: tuple[int, int]) -> None:
        self.dev_console = dev_console
        self.font = dev_console.font
        self.char_width = self.font.render("A", False, (255, 255, 255)).get_width()
        self.char_height = self.font.render("A", False, (255, 255, 255)).get_height()
        self.surface = pg.Surface(size)
        self.text = ''
        self.clipboard = ''
        self.max_chars = self.surface.get_width()//self.char_width - 1
        self.caret_position = 0
        self.draw_caret = True
        self.selection_range = None
        self.history: list[str] = []
        self.history_index = 0
        self.color = (255, 255, 255)
        self.rect = pg.Rect((0, 0), self.surface.get_size())

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.TEXTINPUT and len(self.text) < self.max_chars:
            if self.selection_range:
                self.erase_selection_range()
            self.text = self.text[0:self.caret_position] + event.text + self.text[self.caret_position:]
            self.caret_position += 1
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text:
                    self.dev_console.handle_command(self.text)
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
                    self.move_caret(-1, holding_ctrl=event.mod & pg.KMOD_CTRL, delete=True)
            elif event.key == pg.K_DELETE:
                if self.selection_range:
                    self.erase_selection_range()
                else:
                    self.move_caret(1, holding_ctrl=event.mod & pg.KMOD_CTRL, delete=True)
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
                    self.clipboard = self.text[min(self.selection_range):max(self.selection_range)]
            elif event.key == pg.K_x and event.mod & pg.KMOD_CTRL:
                if self.selection_range and self.selection_range[0] != self.selection_range[1]:
                    self.clipboard = self.text[min(self.selection_range):max(self.selection_range)]
                    self.erase_selection_range()
            elif event.key == pg.K_v and event.mod & pg.KMOD_CTRL:
                if clipboard := self.clipboard:
                    if self.selection_range:
                        self.erase_selection_range()
                    self.text = self.text[:self.caret_position] + clipboard + self.text[self.caret_position:]
                    self.move_caret(len(clipboard))

    def move_caret(self, amount: int, holding_shift: bool = False, holding_ctrl: bool = False, delete=False):
        original_position = self.caret_position
        if holding_ctrl:
            if amount > 0:
                space_index = self.text.find(' ', self.caret_position)
                space_index = space_index if space_index != -1 else len(self.text)
            elif amount < 0:
                space_index = self.text.rfind(' ', 0, max(0, self.caret_position - 1))
            else:
                return
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
            self.text = self.text[:min(self.caret_position, original_position)] + self.text[max(self.caret_position,
                                                                                                original_position):]
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
        self.surface.blit(text_surface, (self.char_width // 3, 5))

    def render_caret(self):
        x = self.char_width * (self.caret_position + 1 / 3)
        pg.draw.line(self.surface, self.color, (x, self.char_height // 6),
                     (x, self.rect.height - self.char_height // 6), 2)

    def render_selection(self):
        x = int(self.char_width * (min(self.selection_range) + 1 / 3))
        y = self.char_height // 8
        w = self.char_width * (max(self.selection_range) - min(self.selection_range))
        h = self.rect.height - 2 * self.char_height // 8
        pixels = pg.surfarray.pixels3d(self.surface)
        pixels[x:x + w, y:y + h, 1] = 255 - pixels[x:x + w, y:y + h, 1]

    def render_body(self):
        self.surface.fill(self.dev_console.secondary_color)
        self.render_text()
        if self.selection_range:
            self.render_selection()
        if self.draw_caret and not self.selection_range:
            self.render_caret()
        pg.draw.rect(self.surface, self.dev_console.primary_color, self.rect, 2)
