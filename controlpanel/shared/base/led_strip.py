from controlpanel.shared.compatibility import Generator, Callable, Optional, Literal


def interpolate_color(color1: tuple[int, int, int], color2: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (int(color1[0] + (color2[0] - color1[0]) * factor),
            int(color1[1] + (color2[1] - color1[1]) * factor),
            int(color1[2] + (color2[2] - color1[2]) * factor))


def make_looping_line_animator(speed: float,
                               color1: tuple[int, int, int],
                               color2: tuple[int, int, int],
                               ) -> Callable[[float, bytearray, tuple[int, int, int]], Generator[None, None, None]]:
    def animation(update_rate_ms: float,
                  buf: bytearray,
                  rgb_mapping: tuple[int, int, int] = (0, 1, 2),
                  ) -> Generator[None, None, None]:
        mapped_color1 = (color1[rgb_mapping[0]], color1[rgb_mapping[1]], color1[rgb_mapping[2]])
        mapped_color2 = (color2[rgb_mapping[0]], color2[rgb_mapping[1]], color2[rgb_mapping[2]])
        offset_per_update = speed * (update_rate_ms / 1000)
        led_count = len(buf) // 3
        # buf = bytearray(led_count * 3)
        position: float = 0.0

        while True:
            for i in range(led_count):
                dist = abs((i - position) % led_count)
                fade = max(0.0, 1.0 - dist / 3.0)
                color = interpolate_color(mapped_color2, mapped_color1, fade)

                offset = i * 3
                buf[offset + 0] = color[0]
                buf[offset + 1] = color[1]
                buf[offset + 2] = color[2]

            yield None
            position = (position + offset_per_update) % led_count

    return animation


class BaseLEDStrip:
    ANIMATIONS: list[Optional[Callable[[float, bytearray, tuple[int,int,int]], Generator[bytearray, None, None]]]] = [
        None,
        make_looping_line_animator(5.0, (0, 255, 0), (0, 0, 0)),
    ]

    def __init__(self, rgb_order: Literal["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"] = "RGB"):
        index_map: dict[Literal["R", "G", "B"]: int] = {'R': 0, 'G': 1, 'B': 2}
        self._rgb_mapping: tuple[int, int, int] = (index_map[rgb_order[0]],
                                                   index_map[rgb_order[1]],
                                                   index_map[rgb_order[2]])
