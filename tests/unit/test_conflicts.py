"""Conflict detection: dot must warn at plan time and exit without mutating."""

import os
import sys

import pytest

sys.path = [p for p in sys.path if not p.endswith("bin")]

from dot import dot  # noqa


def make_profile(root, name, files):
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    for fname, content in files.items():
        path = profile / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return profile


@pytest.mark.parametrize("dry_run", [False, True])
def test_existing_file_conflict(root, dry_run, capsys):
    home = root / "home"
    profile = make_profile(root, "default", {"bashrc": "set -o vi"})
    (home / ".bashrc").write_text("existing")

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=dry_run)

    assert "not a link" in capsys.readouterr().err
    assert (home / ".bashrc").read_text() == "existing"
    assert not (home / ".bashrc").is_symlink()


def test_wrong_target_conflict(root, capsys):
    home = root / "home"
    profile = make_profile(root, "default", {"bashrc": "set -o vi"})
    other = root / "other"
    other.write_text("other")
    (home / ".bashrc").symlink_to(other)

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False)

    assert "instead of" in capsys.readouterr().err
    assert (home / ".bashrc").readlink() == other


def test_duplicate_profiles_conflict(root, capsys):
    home = root / "home"
    profile = make_profile(root, "default", {"bashrc": "set -o vi"})

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(profile), str(profile)], recursive=1, dry_run=False)

    assert "planned more than once" in capsys.readouterr().err
    assert not (home / ".bashrc").is_symlink()


def test_colliding_profiles_conflict(root, capsys):
    home = root / "home"
    one = make_profile(root, "one", {"bashrc": "set -o vi"})
    two = make_profile(root, "two", {"bashrc": "set -o emacs"})

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(one), str(two)], recursive=1, dry_run=False)

    assert "planned more than once" in capsys.readouterr().err
    assert not (home / ".bashrc").is_symlink()


def test_dangling_symlink_conflict_then_unlink(root, capsys):
    home = root / "home"
    profile = make_profile(root, "default", {"bashrc": "set -o vi"})
    gone = root / "gone"
    gone.write_text("temp")
    (home / ".bashrc").symlink_to(gone)
    gone.unlink()

    # Dangling link pointing elsewhere: link must conflict, not crash on apply.
    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False)
    assert "instead of" in capsys.readouterr().err
    assert (home / ".bashrc").is_symlink()

    # Dangling link owned by the profile (e.g. .rendered deleted after a
    # fresh clone): unlink must still remove it.
    (home / ".bashrc").unlink()
    (home / ".bashrc").symlink_to(profile / "bashrc")
    (profile / "env.template").write_text("export A=$A")
    (home / ".env").symlink_to(profile / "env.rendered")
    dot(command="unlink", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False)
    assert not (home / ".env").is_symlink()
    assert not (home / ".bashrc").is_symlink()


def test_rendered_symlink_conflict(root, capsys):
    home = root / "home"
    profile = make_profile(root, "default", {"env.template": "export A=$A"})
    victim = home / "victim"
    victim.write_text("precious")
    (profile / "env.rendered").symlink_to(victim)

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False)

    assert "is a link" in capsys.readouterr().err
    assert victim.read_text() == "precious"


def test_render_preserves_permissions(root):
    home = root / "home"
    profile = make_profile(root, "default", {"env.template": "export A=$A"})
    (profile / "env.template").chmod(0o600)

    dot(command="link", home=str(home), profiles=[str(profile)], recursive=1, dry_run=False)

    mode = os.stat(profile / "env.rendered").st_mode & 0o777
    assert mode == 0o600
