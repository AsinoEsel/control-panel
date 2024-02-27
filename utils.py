import numpy as np
from scipy.ndimage.filters import uniform_filter

def break_up_string(input_string: str, max_chars: int):
    # Find the last space before or at the nth character
    last_space_index = input_string.rfind(' ', 0, max_chars)
    
    if last_space_index < 2:
        return input_string[0:max_chars], input_string[max_chars:]
    
    # Split the string into two parts
    return input_string[:last_space_index], input_string[last_space_index+1:]  # +1 for removing ' '

def break_up_string_into_lines(string: str, max_length: int) -> list[str]:
    if len(string) <= max_length:
        return [string, ]
    lines = []
    while len(string) > max_length:  # Continue until the string is empty or only contains whitespace
        first_half, second_half = break_up_string(string, max_length)
        lines.append(first_half)
        string = second_half  # Prepare the remaining part of the string for the next iteration
    lines.append(second_half)
    return lines

def scale_resolution(input_resolution: tuple[int,int], target_resolution: tuple[int,int]) -> tuple[int,int]:
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

    return (upscaled_width, upscaled_height)

if __name__ == "__main__":
    from window_manager_setup import DEBUG_LONG_TEXT
    print(break_up_string_into_lines(DEBUG_LONG_TEXT, 59))
    