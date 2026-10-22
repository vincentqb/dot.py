"""Conflict detection: dot must warn at plan time and exit without mutating."""

import os
import sys
from pathlib import Path

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
        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=dry_run)

    assert "not a link" in capsys.readouterr().err
    assert (home / ".bashrc").read_text() == "existing"
    assert not (home / ".bashrc").is_symlink()


@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_wrong_target_conflict(root, capsys, command, dry_run):
    home = root / "home"
    profile = make_profile(root, "default", {"bashrc": "set -o vi"})
    other = root / "other"
    other.write_text("other")
    (home / ".bashrc").symlink_to(other)

    with pytest.raises(SystemExit):
        dot(command=command, home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=dry_run)

    assert "instead of" in capsys.readouterr().err
    assert (home / ".bashrc").readlink() == other


@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("target_kind", ["absolute_alias", "relative_alias", "relative"])
@pytest.mark.parametrize(
    "source_name,link_name,files",
    [
        ("bashrc", "bashrc", {"bashrc": "set -o vi"}),
        ("config", "config", {"config/settings": "value"}),
        ("env.rendered", "env", {"env.template": "export A=1"}),
    ],
    ids=["file", "directory", "dangling_template"],
)
def test_equivalent_symlink_target(
    root, capsys, monkeypatch, command, dry_run, target_kind, source_name, link_name, files
):
    home = root / "home"
    profile = make_profile(root, "default", files)
    alias = root / "profile-alias"
    alias.symlink_to(profile, target_is_directory=True)
    actual = (profile if target_kind == "relative" else alias) / source_name
    if target_kind.startswith("relative"):
        actual = Path(os.path.relpath(actual, home))
    link = home / f".{link_name}"
    link.symlink_to(actual)
    monkeypatch.chdir(root)

    dot(command=command, home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=dry_run)

    assert "instead of" not in capsys.readouterr().err
    assert link.is_symlink() == (command == "link" or dry_run)
    if link.is_symlink():
        assert link.readlink() == actual
    if source_name == "env.rendered":
        assert (profile / source_name).exists() == (command == "link" and not dry_run)


def test_duplicate_profiles_conflict(root, capsys):
    home = root / "home"
    profile = make_profile(root, "default", {"bashrc": "set -o vi"})

    with pytest.raises(SystemExit):
        dot(
            command="link",
            home=str(home),
            profiles=[str(profile), str(profile)],
            prefix=".",
            recursive=1,
            dry_run=False,
        )

    assert f"More than one profile modifies file {home / '.bashrc'}." in capsys.readouterr().err
    assert not (home / ".bashrc").is_symlink()


def test_colliding_profiles_conflict(root, capsys):
    home = root / "home"
    one = make_profile(root, "one", {"bashrc": "set -o vi"})
    two = make_profile(root, "two", {"bashrc": "set -o emacs"})

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(one), str(two)], prefix=".", recursive=1, dry_run=False)

    assert f"More than one profile modifies file {home / '.bashrc'}." in capsys.readouterr().err
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
        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    assert "instead of" in capsys.readouterr().err
    assert (home / ".bashrc").is_symlink()

    # Dangling link owned by the profile (e.g. .rendered deleted after a
    # fresh clone): unlink must still remove it.
    (home / ".bashrc").unlink()
    (home / ".bashrc").symlink_to(profile / "bashrc")
    (profile / "env.template").write_text("export A=$A")
    (home / ".env").symlink_to(profile / "env.rendered")
    dot(command="unlink", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    assert not (home / ".env").is_symlink()
    assert not (home / ".bashrc").is_symlink()


@pytest.mark.parametrize("kind", ["link", "directory"])
def test_rendered_not_a_file_conflict(root, capsys, kind):
    home = root / "home"
    profile = make_profile(root, "default", {"env.template": "export A=$A"})
    victim = home / "victim"
    victim.write_text("precious")
    if kind == "link":
        (profile / "env.rendered").symlink_to(victim)
    else:
        (profile / "env.rendered").mkdir()

    with pytest.raises(SystemExit):
        dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)

    assert f"exists but is a {kind}" in capsys.readouterr().err
    assert victim.read_text() == "precious"
    assert list(home.iterdir()) == [victim]


@pytest.mark.parametrize("change", ["content", "mode"])
def test_stale_render_is_updated(root, change):
    home = root / "home"
    profile = make_profile(root, "default", {"env.template": "export A=1"})
    template, rendered = profile / "env.template", profile / "env.rendered"

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)
    if change == "content":
        template.write_text("export A=2")
    else:
        template.chmod(0o600)
    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)

    assert rendered.read_text() == template.read_text()
    assert rendered.stat().st_mode == template.stat().st_mode


def test_render_preserves_permissions(root):
    home = root / "home"
    profile = make_profile(root, "default", {"env.template": "export A=$A"})
    (profile / "env.template").chmod(0o600)

    dot(command="link", home=str(home), profiles=[str(profile)], prefix=".", recursive=1, dry_run=False)

    mode = os.stat(profile / "env.rendered").st_mode & 0o777
    assert mode == 0o600
