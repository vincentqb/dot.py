import subprocess

import pytest
from conftest import skipna

# Test each of:
# dot.py --help
# ./dot.py --help
# PYTHONPATH=./ python -m dot --help


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [None, False, True])
def test_error_code_cli(cli, root, command, home_folder, dry_run):
    home = root / home_folder
    profile = root / "not_a_profile"

    call = cli.split(" ") + [command, "--home", str(home), str(profile)]

    if dry_run is not None:
        if dry_run:
            call += ["--dry-run"]
        else:
            call += ["--no-dry-run"]

    result = subprocess.run(call, check=False, capture_output=True, text=True)

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

    call = cli.split(" ") + command + ["-h"]
    error_code = subprocess.call(call)
    assert error_code == 0


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("command", [None, "link", "unlink"])
def test_error_code_missing_cli(cli, root, command):
    command = [command] if command else []

    call = cli.split(" ") + command
    error_code = subprocess.call(call)
    assert error_code == 2


@pytest.mark.parametrize("cli", [skipna("dot.py"), skipna("./dot.py"), "python -m dot"])
@pytest.mark.parametrize("args,prefix", [([], "."), (["--prefix", "_"], "_"), (["-p", "_"], "_")])
def test_prefix_cli(cli, root, args, prefix):
    home = root / "home"
    profile = root / "default"
    profile.mkdir()
    (profile / "bashrc").write_text("set -o vi")

    call = cli.split(" ") + ["link", "--home", str(home), str(profile)] + args
    error_code = subprocess.call(call)

    assert error_code == 0
    assert (home / f"{prefix}bashrc").is_symlink()


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

    call = cli.split(" ") + [
        command,
        *args,
        "--home",
        str(home),
        "-r",
        "--dry-run" if dry_run else "--no-dry-run",
        str(profile),
    ]
    result = subprocess.run(call, check=False, capture_output=True, text=True)

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

    call = cli.split(" ") + ["link", option, "--home", str(home), str(profile)]
    result = subprocess.run(call, check=False, capture_output=True, text=True)

    assert result.returncode == 2
    assert "expected one argument" in result.stderr
    assert list(home.iterdir()) == []
