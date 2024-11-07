from controlpanel.scripts import ControlAPI, Event
from controlpanel.gui.widgets import Desktop, Log
from fourteensegment import Display, rgb_to_b16
from itertools import islice
from typing import Generator


display = Display(display_number=4)
UNIVERSE = 14
MEMORY_INDEX = 1
NUMBER_OF_DIGITS = 8

COLOR = (255, 0, 0)


class Frame:
    def __init__(self, text: str, color: tuple[int, int, int]) -> None:
        self.text = text
        self.color = color


class Animation:
    def __init__(self, frequency: float | int | None) -> None:
        self.get_frame = self.frame_generator()
        self.frequency = frequency

    def frame_generator(self) -> Generator[Frame, None, None]:
        while True:
            yield Frame("", (0, 0, 0))


class StaticText(Animation):
    def __init__(self, text: str, color: tuple[int, int, int]):
        super().__init__(None)
        self.text = text
        self.color = color

    def frame_generator(self) -> Generator[Frame, None, None]:
        while True:
            yield Frame(self.text, self.color)


class ScrollingText(Animation):
    def __init__(self, text: str, color: tuple[int, int, int], wrapper: str = " ", frequency: float = 2.0,
                 starting_position: int = 10):
        super().__init__(frequency)
        self.text = text + wrapper
        self.color = color
        self.position = starting_position % len(self.text)

    def frame_generator(self) -> Generator[Frame, None, None]:
        while True:
            self.position = (self.position + 1) % len(self.text)
            scrolled_text = ""
            for i in range(NUMBER_OF_DIGITS):
                scrolled_text += self.text[(i + self.position) % len(self.text)]
            yield Frame(scrolled_text, self.color)


@ControlAPI.callback("TerminalInputBox", "TextInput")
def console(event: Event):
    desktop: Desktop = ControlAPI.window_manager.desktops.get("main")
    log: Log = desktop.widget_manifest.get("TerminalLog")
    user_input = event.value

    if user_input.startswith("/color"):
        h = user_input.removeprefix("/color").lstrip("# ")
        if not h:
            log.print_to_log("Usage: /color <HEX_VALUE>.")
            return
        if len(h) != 6 or not all(digit in "0123456789ABCDEF" for digit in h):
            log.print_to_log(f"#{h} is an invalid hex code.")
            return
        global COLOR
        COLOR = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        log.print_to_log(f"Changing color to {h}")
    elif user_input.startswith("/display"):
        text_to_display = user_input.lstrip().removeprefix("/display").lstrip().upper()
        if not text_to_display:
            log.print_to_log("Usage: /display <message>")
            return
        log.print_to_log(f"Sending {text_to_display} to display...")

        anim = ScrollingText(text_to_display, COLOR)
        slice_length = int(10 * 3)
        anim = [(frame.text, rgb_to_b16(*frame.color)) for frame in islice(anim.get_frame, slice_length)]
        display.memory(UNIVERSE, MEMORY_INDEX, anim, period=int(1000 / 3))
        display.show(MEMORY_INDEX)
    elif user_input.startswith("/help"):
        return
    elif user_input.startswith("/"):
        split = user_input.split(" ")
        log.print_to_log(f"Unknown command: {split[0]}")
    else:
        log.print_to_log(user_input)
