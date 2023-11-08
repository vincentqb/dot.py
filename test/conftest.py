import contextlib
import os
from pathlib import Path

import pytest


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
