import contextlib
import os
from pathlib import Path
from shutil import which

import pytest


def is_not_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is None


@contextlib.contextmanager
def set_env(**environ):
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


@pytest.fixture
def root(tmp_path):
    root = Path(str(tmp_path))
    home = root / "home"
    home.mkdir(parents=True)
    yield root
