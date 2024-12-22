import time
import pygame as pg
import os
import inspect
from typing import get_type_hints, TYPE_CHECKING, Callable, Any, Union
from itertools import islice
import types
import sys
from collections import deque
if TYPE_CHECKING:
    from controlpanel.game_manager import GameManager, BaseGame


ColorType = tuple[int, int, int]


class OutputRedirector:
    stdout = sys.stdout

    def __init__(self, *custom_redirects: Callable[[str], None]):
        self.custom_redirects: tuple[Callable[[str], None], ...] = custom_redirects

    def write(self, text):
        self.stdout.write(text)
        if text.strip():  # Ignore empty lines
            for redirect in self.custom_redirects:
                redirect(text)

    def flush(self):
        self.stdout.flush()


def console_command(*aliases: str, is_cheat_protected: bool = False, show_return_value: bool = False):
    # This cursed if statement ensures that the decorator works even when used without parentheses
    if len(aliases) == 1 and callable(aliases[0]) and not isinstance(aliases[0], str):
        f = aliases[0]
        f._is_console_command = True
        return f

    def decorator(func):
        func._is_console_command = True
        func._aliases = aliases
        func._is_cheat_protected = is_cheat_protected
        func._show_return_value = show_return_value
        return func
    return decorator


class Logger:
    def __init__(self,
                 screen_surface: pg.Surface,
                 max_relative_height: float = 0.3,
                 *,
                 font_name: str = os.path.join(os.path.dirname(__file__), "..", "scripts", "gui", "media", "clacon2.ttf"),
                 font_size: int = 20
                 ):
        self.font = pg.font.Font(font_name, font_size)
        max_lines = int(screen_surface.get_height() * max_relative_height / self.font.get_height())

        self.surface = pg.Surface((screen_surface.get_width(), max_lines * self.font.get_height()), flags=pg.SRCALPHA)
        self.surface.fill((0, 0, 0, 0))

        self.max_alpha: int = 200
        self.fade_start_time = 5.0
        self.fade_duration = 2.0

        self.log: deque[tuple[str, float]] = deque((("", 0.0) for _ in range(max_lines)), maxlen=max_lines)

    def print(self, text: str):
        self.log.append((text, time.time()))

    def render(self, surface: pg.Surface):
        self.surface.fill((0, 0, 0, 0))
        current_time: float = time.time()
        for i, (text, timestamp) in enumerate(reversed(self.log)):
            age: float = current_time - timestamp
            if age > self.fade_start_time + self.fade_duration:
                continue
            if age > self.fade_start_time:
                alpha = int(pg.math.lerp(self.max_alpha, 0.0, (age - self.fade_start_time) / self.fade_duration))
            else:
                alpha = self.max_alpha
            font_surface = self.font.render(text, True, (255, 255, 255))
            font_surface.set_alpha(alpha)
            self.surface.blit(font_surface, (0, self.surface.get_height() - (i+1) * font_surface.get_height()))
        surface.blit(self.surface, (0, surface.get_height() - self.surface.get_height()))


class DeveloperConsole:
    DEFAULT_HEIGHT = 200

    def __init__(self,
                 game_manager: "GameManager",
                 render_size: tuple[int, int],
                 *,
                 font_name: str = os.path.join(os.path.dirname(__file__), "..", "scripts", "gui", "media", "clacon2.ttf"),
                 font_size: int = 20):
        self.font = pg.font.Font(font_name, font_size)
        self.game_manager = game_manager
        self.open: bool = False
        self.dark_surface = pg.Surface(render_size)
        self.dark_surface.fill((100, 100, 100))

        self.primary_color = (76, 88, 68)
        self.secondary_color = (62, 70, 55)
        self.primary_text_color = (255, 255, 255)
        self.secondary_text_color = (216, 222, 211)
        self.border_color_dark = (40, 46, 34)
        self.border_color_bright = (136, 145, 128)
        self.highlight_color = (150, 135, 50)
        self.error_color = (255, 64, 64)

        self.char_width = self.font.render("A", False, (255, 255, 255)).get_width()
        self.char_height = self.font.get_height()
        self.border_offset = 6

        self.surface = pg.Surface((render_size[0], self.DEFAULT_HEIGHT))

        input_box_height = int(self.char_height * 1.5)
        log_width = input_box_width = render_size[0] - 2 * self.border_offset
        max_log_height = render_size[0] - input_box_height - 3 * self.border_offset

        self.input_box = InputBox(self, (input_box_width, input_box_height))
        self.log = Log(self, (log_width, max_log_height))

    @staticmethod
    def find_commands(instance: Union["GameManager", "BaseGame", "DeveloperConsole"]) -> dict[str: Callable[..., Any]]:
        commands = dict()
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            if not getattr(method, "_is_console_command", False):
                continue
            aliases = getattr(method, "_aliases", False)
            if aliases is not False and len(aliases) > 0:
                for alias in aliases:
                    commands[alias] = method
            else:
                commands[name] = method
        return commands

    def get_all_commands(self) -> dict[str: Callable[..., Any]]:
        return (self.find_commands(self) |
                self.find_commands(self.game_manager) |
                self.find_commands(self.game_manager.get_game()))

    def list_all_commands(self):
        all_commands = (self.find_commands(self) |
                        self.find_commands(self.game_manager) |
                        self.find_commands(self.game_manager.get_game())).keys()
        if not all_commands:
            self.log.print("No console commands found.", color=self.error_color, mirror_to_stdout=True)
            return
        self.log.print("List of all available commands: (type help <command> for help)", mirror_to_stdout=True)
        column_gap = 2
        column_width = max(len(command_name) for command_name in all_commands) + column_gap
        column_count = self.input_box.max_chars // column_width
        command_iterator = iter(all_commands)
        while True:
            chunk = list(islice(command_iterator, column_count))
            if not chunk:
                break
            self.log.print("".join(f"{command_name:<{column_width}}" for command_name in chunk),
                           color=self.secondary_text_color, mirror_to_stdout=True)

    @console_command
    def help(self, command_name: str = None) -> None:
        if not command_name:
            self.list_all_commands()
        elif (command := self.get_all_commands().get(command_name)) is not None:
            if command.__doc__:
                self.log.print(command.__doc__.strip(), mirror_to_stdout=True)
            self.print_usage_string(command)
        else:
            self.log.print(
                f"No command {command_name} exists in the game {self.game_manager.get_game().__class__.__name__}.",
                color=self.error_color, mirror_to_stdout=True)
        return

    @console_command
    def clear(self):
        self.log.history.clear()
        self.log.history_index = 0
        self.log.render()

    @console_command(is_cheat_protected=True, show_return_value=True)
    def eval(self, eval_string: str):
        from controlpanel.scripts import ControlAPI
        locals().update({
            "api": ControlAPI,
            "game_manager": self.game_manager,
            "game": self.game_manager.get_game(),
        })
        try:
            return eval(eval_string)
        except (NameError, AttributeError, SyntaxError) as e:
            self.log.print(f"{e.__class__.__name__}: {str(e)}", color=self.error_color, mirror_to_stdout=True)

    @console_command(is_cheat_protected=True)
    def send_dmx(self, device_name: str, *values: int) -> None:
        from controlpanel.scripts import ControlAPI
        data = bytes(values)
        ControlAPI.send_dmx(device_name, data)

    def handle_command(self, command: str, *, suppress_logging: bool = False):
        if not suppress_logging:
            self.log.print(">>> " + command, color=self.primary_text_color, mirror_to_stdout=True)
        command_name, *args = command.split()
        func = self.get_all_commands().get(command_name)
        if func is None:
            self.log.print(f"No command {command_name} exists in the game {self.game_manager._current_game.__class__.__name__}.", color=self.error_color, mirror_to_stdout=True)
            return
        if getattr(func, "_is_cheat_protected", False) and not self.game_manager.cheats_enabled:
            self.log.print(f"The command {command_name} is cheat protected.", mirror_to_stdout=True)
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
                        self.log.print(f"{e.__class__.__name__}: {str(e)}", color=self.error_color, mirror_to_stdout=True)
            return_value = func(*cast_args)
            if getattr(func, "_show_return_value", False):
                self.log.print(str(return_value), mirror_to_stdout=True)
        except TypeError as e:
            self.log.print(f"{e.__class__.__name__}: {str(e)}", color=self.error_color, mirror_to_stdout=True)
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
        self.log.print(string, mirror_to_stdout=True)

    def resize(self, new_height: int = 100):
        new_height = min(self.game_manager._screen.get_height(), max(self.input_box.surface.get_height() + 2 * self.border_offset, new_height))
        self.surface = pg.Surface((self.surface.get_width(), new_height))

    def handle_events(self, events: list[pg.event.Event]):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.game_manager.toggle_dev_console()
            elif event.type == pg.KEYDOWN and (event.key == 1073741921 or event.key == pg.K_PAGEUP):
                self.resize(self.surface.get_height() - 50)
            elif event.type == pg.KEYDOWN and (event.key == 1073741915 or event.key == pg.K_PAGEDOWN):
                self.resize(self.surface.get_height() + 50)
            elif event.type == pg.MOUSEWHEEL:
                self.log.history_index -= event.y
                self.log.history_index = max(0, min(self.log.history_index, len(self.log.history)-1))
                self.log.render()
            else:
                self.input_box.handle_event(event)

    def render(self, surface: pg.Surface):
        self.surface.fill(self.primary_color)

        visible_log_height = self.surface.get_height() - self.input_box.surface.get_height() - 3 * self.border_offset
        self.surface.blit(self.log.surface, (self.border_offset, self.border_offset),
                          (0, self.log.surface.get_height() - visible_log_height, self.log.surface.get_width(), visible_log_height))

        self.input_box.render_body()
        input_box_x, input_box_y = (self.border_offset, self.surface.get_height() - self.input_box.surface.get_height() - self.border_offset)
        self.surface.blit(self.input_box.surface, (input_box_x, input_box_y))

        if visible_log_height > 0:
            self.draw_border_rect(self.surface, (self.border_offset, self.border_offset, self.log.surface.get_width(), visible_log_height), -1, self.border_color_dark, self.border_color_bright)
        self.draw_border_rect(self.surface, (input_box_x, input_box_y, self.input_box.surface.get_width(), self.input_box.surface.get_height()), -1, self.border_color_dark, self.border_color_bright)
        self.draw_border_rect(self.surface, (0, 0, self.surface.get_width(), self.surface.get_height()), 0, self.border_color_bright, self.border_color_dark)

        surface.blit(self.dark_surface, (0, 0), special_flags=pg.BLEND_RGB_MULT)
        surface.blit(self.surface, (0, 0))

    @staticmethod
    def draw_border_rect(surface: pg.Surface, vertices: tuple[int, int, int, int], offset: int, primary_color: ColorType, secondary_color: ColorType):
        pixel_offset = 1 if offset % 2 == 0 else 0
        left, top, width, height = vertices[0] + offset, vertices[1] + offset, vertices[2] - offset - pixel_offset, vertices[3] - offset - pixel_offset
        pg.draw.line(surface, primary_color, (left, top), (left, top+height), 1)
        pg.draw.line(surface, secondary_color, (left+width, top), (left+width, top+height), 1)
        pg.draw.line(surface, primary_color, (left, top), (left+width, top), 1)
        pg.draw.line(surface, secondary_color, (left, top+height), (left+width, top+height), 1)


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

    def print(self, string: str, color: ColorType | None = None, *, mirror_to_stdout: bool = False, append_to_history: bool = True):
        if append_to_history:
            self.history.append((string, color))
            self.history_index = len(self.history)
        if mirror_to_stdout:
            print("DEV: " + string, file=sys.__stdout__)
        color = color if color is not None else self.dev_console.secondary_text_color
        font_surface = self.dev_console.font.render(string, True, color, self.dev_console.secondary_color)
        dy = -font_surface.get_height()
        self.surface.scroll(0, dy)
        self.surface.fill(self.dev_console.secondary_color, (0, self.surface.get_height() + dy, self.surface.get_width(), -dy))
        self.surface.blit(font_surface, (0, self.surface.get_height() - font_surface.get_height()))


class InputBox:
    def __init__(self, dev_console: DeveloperConsole, size: tuple[int, int]) -> None:
        self.dev_console = dev_console
        self.font = dev_console.font
        self.surface = pg.Surface(size)
        self.text = ''
        self.clipboard = ''
        self.max_chars = self.surface.get_width()//self.dev_console.char_width - 1
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
        text_surface = self.font.render(self.text, True, self.color, None)
        self.surface.blit(text_surface, (self.dev_console.char_width // 3, 5))

    def render_caret(self):
        x = self.dev_console.char_width * (self.caret_position + 1 / 3)
        pg.draw.line(self.surface, self.color, (x, self.dev_console.char_height // 6),
                     (x, self.rect.height - self.dev_console.char_height // 6), 2)

    def render_selection(self):
        x = int(self.dev_console.char_width * (min(self.selection_range) + 1 / 3))
        y = self.dev_console.char_height // 8
        w = self.dev_console.char_width * (max(self.selection_range) - min(self.selection_range))
        h = self.rect.height - 2 * self.dev_console.char_height // 8
        pg.draw.rect(self.surface, self.dev_console.highlight_color, (x, y, w, h))

    def render_body(self):
        self.surface.fill(self.dev_console.secondary_color)
        if self.selection_range:
            self.render_selection()
        self.render_text()
        if self.draw_caret and not self.selection_range:
            self.render_caret()
