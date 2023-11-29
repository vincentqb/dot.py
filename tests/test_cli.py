import subprocess

import pytest
from conftest import skipna


@pytest.mark.parametrize("cli", [skipna("dotpy"), skipna("./dotpy"), "python -m dot"])
@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [None, False, True])
def test_error_code_cli(cli, root, command, home_folder, dry_run):
    home = root / home_folder
    profile = root / "not_a_profile"

    error_code = subprocess.call(
        cli.split(" ")
        + [
            command,
            str(home),
            str(profile),
        ]
        + ([] if dry_run is None else [f"--{'' if dry_run else 'no-'}dry-run"])
    )

    assert error_code == 1
    assert home.is_dir() != (home_folder != "home")
    assert not profile.is_dir()


@pytest.mark.parametrize("cli", [skipna("dotpy"), skipna("./dotpy"), "python -m dot"])
@pytest.mark.parametrize("command", ["", "link", "unlink"])
def test_error_code_help_cli(cli, root, command):
    error_code = subprocess.call(cli.split(" ") + ([command] if command else []) + ["-h"])
    assert error_code == 0


@pytest.mark.parametrize("cli", [skipna("dotpy"), skipna("./dotpy"), "python -m dot"])
@pytest.mark.parametrize("command", ["", "link", "unlink"])
def test_error_code_missing_cli(cli, root, command):
    error_code = subprocess.call(cli.split(" ") + ([command] if command else []))
    assert error_code == 2
