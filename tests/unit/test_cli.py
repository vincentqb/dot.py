import os
import subprocess
from pathlib import Path

import pytest
from conftest import skipna

# Test each of:
# dot.py --help
# ./dot.py --help
# PYTHONPATH=./ python -m dot --help


def run_cli(cli, args, *, cwd=None, env=None):
    repository = Path(__file__).resolve().parents[2]
    command = cli.split(" ")
    if command[0] == "./dot.py":
        command[0] = str(repository / "dot.py")
    child_env = {**os.environ, "PYTHONPATH": str(repository), **(env or {})}
    return subprocess.run(command + args, check=False, capture_output=True, text=True, cwd=cwd, env=child_env)


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [None, False, True])
def test_error_code_cli(cli, root, command, home_folder, dry_run):
    home = root / home_folder
    profile = root / "not_a_profile"

    call = [command, "--home", str(home), str(profile)]

    if dry_run is not None:
        if dry_run:
            call += ["--dry-run"]
        else:
            call += ["--no-dry-run"]

    result = run_cli(cli, call)

    assert result.returncode == 1
    # A missing home is reported and the profile is never looked at;
    # with a home present only the missing profile is reported.
    warned, silent = ("Folder", "Profile") if home_folder == "not_a_home" else ("Profile", "Folder")
    assert warned in result.stderr
    assert silent not in result.stderr
    assert home.is_dir() != (home_folder != "home")
    assert not profile.is_dir()


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("command", [None, "link", "unlink"])
def test_error_code_help_cli(cli, root, command):
    command = [command] if command else []

    result = run_cli(cli, command + ["-h"])
    assert result.returncode == 0
    if command:
        assert "--home" in result.stdout
        assert "--prefix" in result.stdout


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("command", [None, "link", "unlink"])
def test_error_code_missing_cli(cli, root, command):
    command = [command] if command else []

    result = run_cli(cli, command)
    assert result.returncode == 2


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize(
    "option,prefix", [(None, "."), ("--prefix", "."), ("--prefix", "_"), ("-p", "_"), ("--prefix", "")]
)
def test_prefix_cli(cli, root, option, prefix):
    home = root / "home"
    profile = root / "default"
    profile.mkdir()
    (profile / "bashrc").write_text("set -o vi")

    args = [option, prefix] if option else []
    result = run_cli(cli, ["link", str(profile), *args], env={"HOME": str(home)})

    assert result.returncode == 0, result.stderr
    assert (home / f"{prefix}bashrc").is_symlink()


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
def test_home_path_with_spaces_cli(cli, root):
    destination = root / "destination with spaces"
    profile = root / "profile with spaces"
    destination.mkdir()
    profile.mkdir()
    source = profile / "bashrc"
    source.write_text("set -o vi")

    result = run_cli(cli, ["link", "--home", str(destination), str(profile)])

    assert result.returncode == 0, result.stderr
    assert (destination / ".bashrc").readlink() == source


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("home_arg", ["~/.config", "~/.config/"])
def test_selective_config_cli(cli, root, home_arg):
    home = root / "home"
    destination = home / ".config"
    destination.mkdir()
    existing = destination / "unmanaged"
    existing.write_text("local state")
    profile = root / "config"
    (profile / "nvim").mkdir(parents=True)
    (profile / "nvim" / "init.lua").write_text("vim.o.number = true")
    (profile / "starship.toml").write_text("add_newline = false")

    args = [str(profile), "--home", home_arg, "--prefix", ""]
    result = run_cli(cli, ["link", *args], cwd=root, env={"HOME": str(home)})

    assert result.returncode == 0, result.stderr
    assert destination.is_dir() and not destination.is_symlink()
    assert (destination / "nvim").readlink() == profile / "nvim"
    assert (destination / "starship.toml").readlink() == profile / "starship.toml"
    assert existing.read_text() == "local state"
    assert not (profile / "unmanaged").exists()

    result = run_cli(cli, ["unlink", *args], cwd=root, env={"HOME": str(home)})

    assert result.returncode == 0, result.stderr
    assert list(destination.iterdir()) == [existing]
    assert existing.read_text() == "local state"


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("args", [["--prefix", ""], ["-p", ""], ["--prefix="], ["-p="]])
@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_empty_prefix_followed_by_options_cli(cli, root, args, command, dry_run):
    home = root / "home"
    profile = root / "default"
    folder = profile / "folder"
    folder.mkdir(parents=True)
    (profile / "bashrc").write_text("set -o vi")
    (folder / "env.template").write_text("export A=1")
    if command == "unlink":
        (home / "bashrc").symlink_to(profile / "bashrc")
        (home / "folder").symlink_to(folder)

    call = [
        command,
        *args,
        "--home",
        str(home),
        "-r",
        "--dry-run" if dry_run else "--no-dry-run",
        str(profile),
    ]
    result = run_cli(cli, call, cwd=root)

    assert result.returncode == 0, result.stderr
    linked = (command == "link") != dry_run
    assert (home / "bashrc").is_symlink() == linked
    assert (home / "folder").is_symlink() == linked
    assert not (home / ".bashrc").is_symlink()
    assert not (home / ".folder").is_symlink()
    if command == "link":
        assert (folder / "env.rendered").exists() == (not dry_run)
        assert (folder / "env").is_symlink() == (not dry_run)
        if not dry_run:
            assert (home / "folder" / "env").read_text() == "export A=1"


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("option", ["--prefix", "-p"])
def test_missing_prefix_value_cli(cli, root, option):
    home = root / "home"
    profile = root / "default"
    profile.mkdir()
    (profile / "bashrc").write_text("set -o vi")

    result = run_cli(cli, ["link", option, "--dry-run", str(profile)])

    assert result.returncode == 2
    assert "expected one argument" in result.stderr
    assert list(home.iterdir()) == []
