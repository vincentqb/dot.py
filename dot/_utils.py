import os


def capitalize(message):
    return "\n".join(
        ((m[0].upper() if len(m) > 0 else "") + (m[1:] if len(m) > 1 else "") for m in message.split("\n"))
    )


def colorize(message, color):
    COLORS = {
        "blue": "\x1b[36;20m",
        "grey": "\x1b[38;20m",
        "green": "\x1b[32;20m",
        "red": "\x1b[31;20m",
        "red bold": "\x1b[31;1m",
        "reset": "\x1b[0m",
        "yellow": "\x1b[33;20m",
    }
    return COLORS[color] + message + COLORS["reset"]


def get_env(key):
    return os.environ.get(key, "false").lower() in ("true", "t", "1")
