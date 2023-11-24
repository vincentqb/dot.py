import os


def get_env(key):
    return os.environ.get(key, "false").lower() in ("true", "t", "1")
