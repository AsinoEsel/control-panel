import fnmatch
import os

RELATIVE_PATH_TO_IGNORE = '../.webreplignore'

script_dir = os.path.dirname(os.path.abspath(__file__))
path_to_ignore = os.path.join(script_dir, RELATIVE_PATH_TO_IGNORE)


def read_ignore_patterns(filename) -> list[str]:
    """Read patterns from a file and return them as a list."""
    with open(filename, 'r') as file:
        patterns = file.readlines()
    return [pattern.strip() for pattern in patterns if pattern.strip() and not pattern.startswith('#')]


def should_ignore(file, patterns) -> bool:
    """Determine if the file matches any of the ignore patterns."""
    return any(fnmatch.fnmatch(file, pattern) for pattern in patterns)


ALWAYS_IGNORE = [path_to_ignore, f"{__name__}.py"]
IGNORE_PATTERNS = read_ignore_patterns(path_to_ignore) + ALWAYS_IGNORE
