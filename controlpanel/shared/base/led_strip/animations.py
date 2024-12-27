import math
import random

try:
    from time import ticks_ms, ticks_diff, ticks_add, time
except ImportError:
    import time
    ticks_ms = lambda: int(time.time() * 1000)
    ticks_diff = lambda x, y: x - y
    ticks_add = lambda x, y: x + y


def interpolate_rgb(color1: tuple[int, int, int], color2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    if not (0.0 <= t <= 1.0):
        raise ValueError("Interpolation factor t must be between 0.0 and 1.0")

    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)

    return r, g, b


def clamp(val, a, b):
    return min(b, max(a, val))


def initialise_rgb_buffer(led_count: int, color: tuple[int, int, int]):
    buffer = bytearray(led_count * 3)
    for led in range(led_count):
        for channel in range(3):
            buffer[led * 3 + channel] = color[channel]
    return buffer


def set_leds_to_color(buffer: bytearray, led_range: range, color: tuple[int, int, int]):
    buffer_length = len(buffer)
    for led in led_range:
        for channel in range(3):
            buffer[(led * 3 + channel) % buffer_length] = color[channel]


def set_leds_to_colors(buffer: bytearray, colors: list[tuple[int, int, int]]):
    for i, color in enumerate(colors):
        for channel in range(3):
            buffer[i * 3 + channel] = color[channel]


def strobe(led_count: int, frequency: float, duty: float, color1: tuple[int, int, int] = (255, 255, 255),
           color2: tuple[int, int, int] = (0, 0, 0)):
    assert len(color1) == len(color2) == 3, "colors need to be RGB tuples"
    duty = clamp(duty, 0.0, 1.0)
    period_ms = int(1000 / frequency)
    buffer1 = initialise_rgb_buffer(led_count, color1)
    buffer2 = initialise_rgb_buffer(led_count, color2)
    while True:
        current_time = ticks_ms()
        yield buffer1 if current_time % period_ms < duty * period_ms else buffer2


def random_strobe(led_count: int, min_strobe_length_ms: int, max_strobe_length_ms: int, min_pause_ms: int,
                  max_pause_ms: int, color1: tuple[int, int, int], color2: tuple[int, int, int]):
    is_strobing = False
    next_strobe_start = 0
    next_strobe_end = 0
    buffer1 = initialise_rgb_buffer(led_count, color1)
    buffer2 = initialise_rgb_buffer(led_count, color2)
    while True:
        current_time = ticks_ms()
        if not is_strobing:
            if ticks_diff(current_time, next_strobe_start) > 0:
                is_strobing = True
                next_strobe_end = ticks_add(current_time, random.randint(min_strobe_length_ms, max_strobe_length_ms))
                yield buffer1
            else:
                yield None
        if is_strobing:
            if ticks_diff(current_time, next_strobe_end) > 0:
                is_strobing = False
                next_strobe_start = ticks_add(current_time, random.randint(min_pause_ms, max_pause_ms))
                yield buffer2
            else:
                yield None


def twinkle(led_count: int):
    """Picks a random color for each LED, then does a sine wave animation on it"""
    buffer = bytearray(led_count * 3)
    colors: list[tuple[float, float, float]] = [(random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)) for _ in range(led_count)]
    while True:
        for i in range(led_count):
            brightness = (math.sin(time()) + 1) * 128
            for channel in range(3):
                buffer[i + channel] = int(brightness * colors[i][channel])
        yield buffer


def scrolling_gradient(led_count: int, color1: tuple[int, int, int], color2: tuple[int, int, int], speed: float):
    buffer = bytearray(led_count * 3)
    while True:
        current_time = time()
        t = (math.sin(speed * current_time) + 1)/2
        new_color = interpolate_rgb(color1, color2, t)
        buffer[3:] = buffer[:-3]
        for i in range(3):
            buffer[i] = new_color[i]
        print(i for i in buffer)
        yield buffer


def looping_line(led_count: int, line_length: int | float, color1: tuple[int, int, int], color2: tuple[int, int, int],
                 period_ms: int):
    if isinstance(line_length, float):
        line_length = clamp(line_length, 0.0, 1.0)
        line_length = int(led_count * line_length)

    clean_buffer = initialise_rgb_buffer(led_count, color2)
    buffer = clean_buffer[::]

    line_start = 0

    next_update_time = 0

    while True:
        current_time = ticks_ms()
        if ticks_diff(current_time, next_update_time) > 0:
            line_start = int(((current_time % period_ms) / period_ms) * led_count)
            buffer = clean_buffer[::]
            set_leds_to_color(buffer, range(line_start, line_start + line_length), color1)
            yield buffer
        else:
            yield None
