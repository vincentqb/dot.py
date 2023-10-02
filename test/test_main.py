import contextlib
import os
import tempfile
from pathlib import Path

import pytest
from dot import dot as main


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
        yield root


def test_link_unlink_profile(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "bashrc"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

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


def test_link_unlink_template_recursive(root):

    if not os.environ.get("DOT_RR", False):
            pytest.xfail("This test is known to fail: rendering is not done recursively.")

    home = root / "home"
    profile = root / "default"
    target = home / ".folder"

    candidate = profile / "folder" / "env.template"
    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
        assert not (candidate.parent / "env").exists()
        assert not (target / "env").exists()
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
        assert (candidate.parent / "env").exists()
        assert (target / "env").exists()

    with open(target / "env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=True)
    assert (candidate.parent / "env").exists()
    assert (target / "env").exists()

    with open(target / "env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=False)
    assert (candidate.parent / "env").exists()
    assert not (target / "env").exists()


def test_link_unlink_template(root):

    home = target = root / "home"
    profile = root / "default"

    candidate = profile / "env.template"
    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
        assert not (profile / "env.rendered").exists()
        assert not (target / ".env").is_symlink()
        main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
        assert (profile / "env.rendered").exists()
        assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=True)
    assert (profile / "env.rendered").exists()
    assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    main(command="unlink", home=str(home), profiles=[str(profile)], dry_run=False)
    assert (profile / "env.rendered").exists()
    assert not (target / ".env").is_symlink()


def test_link_rendered_folder(root):

    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.rendered" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
    assert not (home / ".folder.rendered").is_symlink()
    main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
    assert (home / ".folder.rendered").is_symlink()


def test_link_template_folder(root):

    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.template" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    main(command="link", home=str(home), profiles=[str(profile)], dry_run=True)
    assert not (profile / "folder.rendered").exists()
    assert not (home / ".folder.template").is_symlink()
    main(command="link", home=str(home), profiles=[str(profile)], dry_run=False)
    assert not (profile / "folder.rendered").exists()
    assert (home / ".folder.template").is_symlink()
