from window_manager_setup import *
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

if __name__ == "__main__":
    print(break_up_string_into_lines(DEBUG_LONG_TEXT, 59))
    