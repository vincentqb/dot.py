import sys

import pytest
from conftest import set_env

# Workaround in WSL to drop paths with bin causing circular dependency
sys.path = [p for p in sys.path if not p.endswith("bin")]

from dot import dot  # noqa


@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_system_exit(root, command, home_folder, dry_run, capsys):
    home = root / home_folder
    profile = root / "not_a_profile"

    with pytest.raises(SystemExit):
        dot(
            command=command,
            home=str(home),
            profiles=[str(profile)],
            prefix=".",
            recursive=1,
            dry_run=dry_run,
        )

    err = capsys.readouterr().err.splitlines()
    assert len(err) == 2  # TODO may wish to also show profile warnings
    assert err[0].endswith("does not exist")  # warning
    assert err[1].startswith("Error:")  # error
    assert home.is_dir() != (home_folder != "home")
    assert not profile.is_dir()


def test_link_unlink_profile(root, capsys):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "bashrc"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
    assert not (home / ".bashrc").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    assert (home / ".bashrc").is_symlink()
    capsys.readouterr()  # drain

    # Re-linking an already-correct link with neither flag set: no output
    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    assert capsys.readouterr().err == ""

    # dry_run=True surfaces info (the plan)
    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
    assert "links to" in capsys.readouterr().err

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
    assert (home / ".bashrc").is_symlink()

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
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
        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=2, dry_run=True)
        assert not (candidate.parent / "env.rendered").exists()
        assert not (candidate.parent / "env").exists()
        assert not (target / "env.rendered").exists()
        assert not (target / "env").exists()

        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=2, dry_run=False)
        assert (candidate.parent / "env.rendered").exists()
        assert (candidate.parent / "env").exists()
        assert (target / "env.rendered").exists()
        assert (target / "env").exists()

    with open(target / "env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=2, dry_run=True)
    assert (candidate.parent / "env").exists()
    assert (target / "env").exists()

    with open(target / "env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=2, dry_run=False)
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
        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
        assert not (profile / "env.rendered").exists()
        assert not (target / ".env.rendered").exists()
        assert not (target / ".env").is_symlink()

        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
        assert (profile / "env.rendered").exists()
        assert not (target / ".env.rendered").exists()
        assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
    assert (profile / "env.rendered").exists()
    assert not (target / ".env.rendered").exists()
    assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
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

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
    assert not (home / ".folder.rendered").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    assert (home / ".folder.rendered").is_symlink()


def test_link_template_folder(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.template" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=True)
    assert not (profile / "folder.rendered").exists()
    assert not (home / ".folder.template").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    assert not (profile / "folder.rendered").exists()
    assert (home / ".folder.template").is_symlink()


@pytest.mark.parametrize("prefix", ["_", ""])
def test_link_unlink_prefix(root, prefix):
    home = root / "home"
    profile = root / "default"

    (profile / "folder").mkdir(parents=True)
    (profile / "bashrc").write_text("set -o vi")
    (profile / "env.template").write_text("export A=1")
    (profile / "folder" / "config").write_text("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=prefix, recursive=1, dry_run=False)
    assert (home / f"{prefix}bashrc").is_symlink()
    assert (home / f"{prefix}folder").is_symlink()
    assert (home / f"{prefix}env").read_text() == "export A=1"
    assert not (home / ".bashrc").exists()
    assert not (home / ".folder").exists()
    assert not (home / ".env").exists()

    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=prefix, recursive=1, dry_run=False)
    assert not (home / f"{prefix}bashrc").is_symlink()
    assert not (home / f"{prefix}folder").is_symlink()
    assert not (home / f"{prefix}env").is_symlink()
