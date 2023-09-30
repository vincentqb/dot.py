import contextlib
import os
import tempfile
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
def dotdash_main():
    import importlib.machinery
    import types

    loader = importlib.machinery.SourceFileLoader("dry_run_then_wet_run", "./dotdash")
    mod = types.ModuleType(loader.name)
    loader.exec_module(mod)
    return mod.dry_run_then_wet_run


@pytest.fixture
def root():
    cwd = os.getcwd()
    root = tempfile.TemporaryDirectory()
    os.chdir(root.name)
    path = Path(root.name)

    home = path / "home"
    home.mkdir(parents=True)

    candidate = path / "another" / "bashrc"
    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    yield path

    root.cleanup()
    os.chdir(cwd)


def test_link_unlink_profile(dotdash_main, root):
    dotdash_main(command="link", home=str(root / "home"), profiles=["another"], dry_run=False)
    dotdash_main(command="unlink", home=str(root / "home"), profiles=["another"], dry_run=False)


def test_link_system_exit(dotdash_main, root):
    with pytest.raises(SystemExit):
        dotdash_main(command="link", home=str(root / "home"), profiles=["not_a_profile"], dry_run=False)


def test_link_template(dotdash_main, root):
    candidate = root / "default" / "env.template"
    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        dotdash_main(command="link", home=str(root / "home"), profiles=["default"], dry_run=False)

    with open(root / "default" / "env.rendered", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"
