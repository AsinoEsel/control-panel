def break_up_string(input_string: str, max_chars: int):
    # Find the last space before or at the nth character
    last_space_index = input_string.rfind(' ', 0, max_chars)
    
    if last_space_index < 2:
        return input_string[0:max_chars], input_string[max_chars:]
    
    # Split the string into two parts
    return input_string[:last_space_index], input_string[last_space_index:]

def is_allowed_character(character):
    if len(character) == 0:
        return False
    if character in ("ä", "ö", "ü", "ß", "Ä", "Ö", "Ü", "ẞ"):
        return True
    unicode_value = ord(character)
    return 32 <= unicode_value < 128