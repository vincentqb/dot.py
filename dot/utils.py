import os as _os


def get_env(key):
    return _os.environ.get(key, "false").lower() in ("true", "t", "1")


# Define colors
RESET = "\x1b[0m"
RED = "\x1b[31;20m"
BOLD_RED = "\x1b[31;1m"
GREEN = "\x1b[32;20m"
YELLOW = "\x1b[33;20m"
BLUE = "\x1b[36;20m"
GREY = "\x1b[38;20m"
