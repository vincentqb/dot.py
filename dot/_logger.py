import logging

from ._utils import BOLD_RED, GREY, RED, RESET, YELLOW, capitalize, get_env


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
        record.msg = capitalize(record.msg)
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
