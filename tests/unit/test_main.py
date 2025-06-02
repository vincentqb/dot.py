import sys
from contextlib import redirect_stderr
from io import StringIO

import pytest
from .test_helpers import set_env

# Workaround in WSL to drop paths with bin causing circular dependency
sys.path = [p for p in sys.path if not p.endswith("bin")]

from dot import dot  # noqa


@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_system_exit(root, command, home_folder, dry_run, caplog):
    home = root / home_folder
    profile = root / "not_a_profile"

    with pytest.raises(SystemExit):
        dot(command=command, home=str(home), profiles=[str(profile)], recursive=1, dry_run=dry_run, verbose=0)

    assert len(caplog.records) == 2  # TODO may wish to also show profile warnings
    assert caplog.records[0].msg.startswith("\x1b[33;20m")
    assert caplog.records[0].msg.endswith("\x1b[0m")
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[1].msg.startswith("\x1b[31;20m")
    assert caplog.records[1].msg.endswith("\x1b[0m")
    assert caplog.records[1].levelname == "ERROR"
    assert home.is_dir() != (home_folder != "home")
    assert not profile.is_dir()


def test_link_unlink_profile(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "bashrc"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=True, verbose=0)
    assert not (home / ".bashrc").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
    assert (home / ".bashrc").is_symlink()

    with redirect_stderr(StringIO()) as captured:
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
    captured = captured.getvalue().split("\n")
    assert len(captured) == 1

    with redirect_stderr(StringIO()) as captured:
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=1)
    captured = captured.getvalue().split("\n")
    assert len(captured) == 1

    with redirect_stderr(StringIO()) as captured:
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=2)
    captured = captured.getvalue().split("\n")
    assert len(captured) == 1

    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=1, dry_run=True, verbose=0)
    assert (home / ".bashrc").is_symlink()

    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
    assert not (home / ".bashrc").is_symlink()


def test_link_unlink_template_recursive(root):
    home = root / "home"
    profile = root / "default"
    target = home / ".folder"
    candidate = profile / "folder" / "env.template"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=2, dry_run=True, verbose=0)
        assert not (candidate.parent / "env.rendered").exists()
        assert not (candidate.parent / "env").exists()
        assert not (target / "env.rendered").exists()
        assert not (target / "env").exists()

        dot(command="link", home=str(home), profiles=[str(profile)], recursive=2, dry_run=False, verbose=0)
        assert (candidate.parent / "env.rendered").exists()
        assert (candidate.parent / "env").exists()
        assert (target / "env.rendered").exists()
        assert (target / "env").exists()

    with open(target / "env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=2, dry_run=True, verbose=0)
    assert (candidate.parent / "env").exists()
    assert (target / "env").exists()

    with open(target / "env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=2, dry_run=False, verbose=0)
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
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=True, verbose=0)
        assert not (profile / "env.rendered").exists()
        assert not (target / ".env.rendered").exists()
        assert not (target / ".env").is_symlink()

        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
        assert (profile / "env.rendered").exists()
        assert not (target / ".env.rendered").exists()
        assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=1, dry_run=True, verbose=0)
    assert (profile / "env.rendered").exists()
    assert not (target / ".env.rendered").exists()
    assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
    assert (profile / "env.rendered").exists()
    assert not (target / ".env.rendered").exists()
    assert not (target / ".env").is_symlink()


def test_link_rendered_folder(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.rendered" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=True, verbose=0)
    assert not (home / ".folder.rendered").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
    assert (home / ".folder.rendered").is_symlink()


def test_link_template_folder(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.template" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=True, verbose=0)
    assert not (profile / "folder.rendered").exists()
    assert not (home / ".folder.template").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False, verbose=0)
    assert not (profile / "folder.rendered").exists()
    assert (home / ".folder.template").is_symlink()
