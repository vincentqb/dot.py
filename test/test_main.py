import contextlib
import os
import tempfile
from pathlib import Path

import pytest
from dot import main


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

        candidate = root / "default" / "env.template"
        candidate.parent.mkdir(parents=True)

        with open(candidate, "w") as fp:
            fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

        yield root


def test_link_unlink_profile(root):
    home = root / "home"
    profile = root / "another"

    main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
    assert not (home / ".bashrc").is_symlink()

    main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
    assert (home / ".bashrc").is_symlink()

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=True)
    assert (home / ".bashrc").is_symlink()

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=False)
    assert not (home / ".bashrc").is_symlink()


@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_system_exit(root, command, dry_run):
    home = root / "home"
    profile = root / "not_a_profile"
    with pytest.raises(SystemExit):
        main(command=command, home=str(home), profiles=[str(profile)], dry_run=dry_run)
    assert not (home / "not_a_profile").is_dir()


def test_link_unlink_template(root):

    home = root / "home"
    profile = root / "default"

    with set_env(APP_SECRET_KEY="abc123"):
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
        assert not (profile / "env.rendered").exists()
        assert not (home / ".env").is_symlink()
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
        assert (profile / "env.rendered").exists()
        assert (home / ".env").is_symlink()

    with open(home / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=True)
    assert (home / ".env").is_symlink()
    assert (profile / "env.rendered").exists()

    with open(home / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=False)
    assert not (home / ".env").is_symlink()
    assert (profile / "env.rendered").exists()
