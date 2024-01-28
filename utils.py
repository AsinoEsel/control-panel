def break_up_string(input_string, max_chars):
    # Find the last space before or at the nth character
    last_space_index = input_string.rfind(' ', 0, max_chars)
    
    # If no space is found, or if the last space is at index 0, return the entire string
    if last_space_index <= 0:
        return input_string, ""
    
    # Split the string into two parts
    first_part = input_string[:last_space_index]
    second_part = input_string[last_space_index + 1:]
    
    return first_part, second_part


def is_allowed_character(character):
    if len(character) == 0:
        return False
    if character in ("ä", "ö", "ü", "ß", "Ä", "Ö", "Ü", "ẞ"):
        return True
    unicode_value = ord(character)
    return unicode_value < 128