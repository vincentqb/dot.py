COLORS = {
    "blue": "\x1b[36;20m",
    "green": "\x1b[32;20m",
    "grey": "\x1b[38;20m",
    "red": "\x1b[31;20m",
    "red bold": "\x1b[31;1m",
    "reset": "\x1b[0m",
    "yellow": "\x1b[33;20m",
}


def colorize(message, color):
    return f"{COLORS.get(color, '')}{message}{COLORS['reset']}"


def capitalize(message):
    """
    Capitalize the first word of each line.
    """
    return "\n".join(
        ((m[0].upper() if len(m) > 0 else "") + (m[1:] if len(m) > 1 else "") for m in message.split("\n"))
    )


def standardize(message, color=None):
    return colorize(capitalize(message), color)
