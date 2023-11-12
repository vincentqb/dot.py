import subprocess

import pytest
from conftest import is_not_tool


def skipif(cli):
    return pytest.param(
        cli,
        marks=pytest.mark.skipif(
            is_not_tool(cli),
            reason=f"{cli} not available",
        )
    )

                    
@pytest.mark.parametrize("cli", [skipif("dot.py"), skipif("./dot.py")])
@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_error_code_cli(cli, root, command, home_folder, dry_run):
    home = root / home_folder
    profile = root / "not_a_profile"

    error_code = subprocess.call(
        [
            cli,
            command,
            str(home),
            str(profile),
            f"--{'' if dry_run else 'no-'}dry-run",
        ]
    )

    assert error_code == 1
    assert home.is_dir() != (home_folder != "home")
    assert not profile.is_dir()


@pytest.mark.parametrize("cli", [skipif("dot.py"), skipif("./dot.py")])
@pytest.mark.parametrize("command", ["", "link", "unlink"])
def test_error_code_help_cli(cli, root, command):
    error_code = subprocess.call([cli] + ([command] if command else []) + ["-h"])
    assert error_code == 0


@pytest.mark.parametrize("cli", [skipif("dot.py"), skipif("./dot.py")])
@pytest.mark.parametrize("command", ["", "link", "unlink"])
def test_error_code_missing_cli(cli, root, command):
    error_code = subprocess.call([cli] + ([command] if command else []))
    assert error_code == 2
