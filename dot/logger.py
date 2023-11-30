__all__ = ["get_counting_logger"]
__ALL__ = dir() + __all__

import logging

from .utils import BOLD_RED, GREY, RED, RESET, YELLOW, get_env


def __dir__():
    return __ALL__


class ColoredFormatter(logging.Formatter):
    FORMAT = "%(message)s"
    formats = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: GREY + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def format(self, record):
        format = self.formats.get(record.levelno)
        return logging.Formatter(format).format(record)


class CallCounter:
    def __init__(self, method):
        self.method = method
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self.method(*args, **kwargs)


def get_counting_logger(dry_run):
    level = logging.WARNING
    if get_env("DOT_DEBUG"):
        level = logging.DEBUG
    elif dry_run:
        level = logging.INFO

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(ColoredFormatter())

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)

    logger.warning = CallCounter(logger.warning)
    return logger
