import pygame as pg


ColorType = tuple[int, int, int]


def maprange(value: int | float, start_range: tuple[int | float, int | float], end_range: tuple[int | float, int | float]) -> float:
    w = (value-start_range[0]) / (start_range[1]-start_range[0])
    y = end_range[0] + w * (end_range[1]-end_range[0])
    return y


def get_display_flags(fullscreen: bool, use_shaders: bool) -> int:
    """
    Determines the flags to be passed to pygame.display.set_mode()

    Args:
        fullscreen: whether the game is running in fullscreen mode
        use_shaders: whether the game is using shaders (OpenGL)

    Returns:
    int: The flags to be passed to pygame.display.set_mode()
    """
    flags = 0
    if fullscreen:
        flags |= pg.FULLSCREEN
    if use_shaders:
        flags |= pg.OPENGL | pg.DOUBLEBUF
    if fullscreen and not use_shaders:
        flags |= pg.SCALED
    return flags


def get_output_size(resolution: tuple[int, int], fullscreen: bool, use_shaders: bool, stretch_to_fit: bool) -> tuple[int, int]:
    """
    Determines the optimal display resolution to be passed to pygame.display.set_mode()

    Args:
        resolution: The resolution that the game is rendered at, before any upscaling may occur
        fullscreen: Required to be True if the game is running with pygame.FULLSCREEN flag
        use_shaders: Required to be True if the game is running with pygame.OPENGL flag
        stretch_to_fit: If the game should be stretched to the monitor's resolution. Requires fullscreen and shaders.

    Returns:
    tuple[int, int]: The resolution to be used in pygame.display.set_mode()
    """
    if not fullscreen:
        return resolution

    if not stretch_to_fit:
        return (
            scale_resolution(resolution, (pg.display.Info().current_w, pg.display.Info().current_h))
            if use_shaders
            else resolution
        )

    return (
        (pg.display.Info().current_w, pg.display.Info().current_h)
        if use_shaders
        else resolution
    )


def scale_resolution(input_resolution: tuple[int, int], target_resolution: tuple[int, int]) -> tuple[int, int]:
    """
    Scales an input resolution to fit into a target resolution while maintaining the aspect ratio.

    Parameters:
    input_resolution (tuple[int, int]): The width and height of the input resolution.
    target_resolution (tuple[int, int]): The width and height of the target resolution.

    Returns:
    tuple[int, int]: The upscaled resolution fitting into the target resolution while maintaining the aspect ratio.
    """
    input_width, input_height = input_resolution
    target_width, target_height = target_resolution

    # Calculate the scaling factor for both dimensions
    scale_width = target_width / input_width
    scale_height = target_height / input_height

    # Choose the smaller scaling factor to maintain the aspect ratio
    scale_factor = min(scale_width, scale_height)

    # Calculate the upscaled dimensions
    upscaled_width = int(input_width * scale_factor)
    upscaled_height = int(input_height * scale_factor)

    return upscaled_width, upscaled_height


def draw_border_rect(surface: pg.Surface, vertices: tuple[int, int, int, int], offset: int, primary_color: ColorType, secondary_color: ColorType):
    pixel_offset = 1 if offset % 2 == 0 else 0
    left, top, width, height = vertices[0] + offset, vertices[1] + offset, vertices[2] - offset - pixel_offset, vertices[3] - offset - pixel_offset
    pg.draw.line(surface, primary_color, (left, top), (left, top+height), 1)
    pg.draw.line(surface, secondary_color, (left+width, top), (left+width, top+height), 1)
    pg.draw.line(surface, primary_color, (left, top), (left+width, top), 1)
    pg.draw.line(surface, secondary_color, (left, top+height), (left+width, top+height), 1)
