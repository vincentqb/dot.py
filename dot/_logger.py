import logging

from ._utils import capitalize, colorize, get_env


class ColoredFormatter(logging.Formatter):
    FORMAT = "%(message)s"
    formats = {
        logging.DEBUG: colorize(FORMAT, "grey"),
        logging.INFO: colorize(FORMAT, "grey"),
        logging.WARNING: colorize(FORMAT, "yellow"),
        logging.ERROR: colorize(FORMAT, "red"),
        logging.CRITICAL: colorize(FORMAT, "red bold"),
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
