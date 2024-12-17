import contextlib
import os
from pathlib import Path
from shutil import which

import pytest


def is_not_tool(name):
    """
    Return False if on PATH and marked as executable.
    """
    return which(name) is None


def skipna(cli):
    return pytest.param(
        cli,
        marks=pytest.mark.skipif(
            is_not_tool(cli),
            reason=f"{cli} not available",
        ),
    )


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
