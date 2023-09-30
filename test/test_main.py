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
        root = Path(str(root))
        home = root / "home"
        home.mkdir(parents=True)

        candidate = root / "another" / "bashrc"
        candidate.parent.mkdir(parents=True)
        with open(candidate, "w") as fp:
            fp.write("set -o vi")

        yield root


def test_link_unlink_profile(root):
    home = root / "home"
    profile = root / "another"

    main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
    assert (home / ".bashrc").exists()

    main(command="unlink", home=home, profiles=[profile], dry_run=False)
    assert not (home / ".bashrc").exists()


def test_link_system_exit(root):
    home = root / "home"
    profile = root / "not_a_profile"
    with pytest.raises(SystemExit):
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
    with pytest.raises(SystemExit):
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
    assert not (home / "not_a_profile").is_dir()


def test_link_template(root):

    home = str(root / "home")

    profile = root / "default"
    profile.mkdir(parents=True)
    candidate = profile / "env.template"

    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)

    with open(profile / "env.rendered", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"
