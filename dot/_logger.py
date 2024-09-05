import logging

from ._utils import standardize


class ColoredFormatter(logging.Formatter):
    FORMAT = "%(message)s"
    formats = {
        logging.DEBUG: standardize(FORMAT, "grey"),
        logging.INFO: standardize(FORMAT, "green"),
        logging.WARNING: standardize(FORMAT, "yellow"),
        logging.ERROR: standardize(FORMAT, "red"),
        logging.CRITICAL: standardize(FORMAT, "red bold"),
    }

    def format(self, record):
        format = self.formats.get(record.levelno)
        record.msg = standardize(record.msg)
        return logging.Formatter(format).format(record)


class CallCounter:
    def __init__(self, method):
        self.method = method
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self.method(*args, **kwargs)


def get_counting_logger(verbose):
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(ColoredFormatter())

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)

    logger.warning = CallCounter(logger.warning)
    return logger
