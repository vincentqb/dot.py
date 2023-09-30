import contextlib
import os
import tempfile
from pathlib import Path

import pytest
from dot import dry_run_then_wet_run as main


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
def root():
    with tempfile.TemporaryDirectory() as root:
        path = Path(str(root))
        home = path / "home"
        home.mkdir(parents=True)

        candidate = path / "another" / "bashrc"
        candidate.parent.mkdir(parents=True)
        with open(candidate, "w") as fp:
            fp.write("set -o vi")

        yield path


def test_link_unlink_profile(root):
    home = str(root / "home")
    profile = str(root / "another")
    main(command="link", home=home, profiles=[profile], dry_run=False)
    main(command="unlink", home=home, profiles=[profile], dry_run=False)


def test_link_system_exit(root):
    home = str(root / "home")
    profile = str(root / "not_a_profile")
    with pytest.raises(SystemExit):
        main(command="link", home=home, profiles=[profile], dry_run=False)


def test_link_template(root):

    profile = root / "default"
    profile.mkdir(parents=True)
    candidate = profile / "env.template"

    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    home_str = str(root / "home")
    profile_str = str(root / "default")

    with set_env(APP_SECRET_KEY="abc123"):
        main(command="link", home=home_str, profiles=[profile_str], dry_run=False)

    with open(profile / "env.rendered", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"
