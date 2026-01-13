#!/usr/bin/env python3

import importlib.metadata
import subprocess
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # ty: ignore


def get_version_from_git():
    cmd = "git describe --tags --abbrev=0".split()
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not get version from git\nCaptured stdout:\n{result.stdout}\nCaptured stderr:\n{result.stderr}"
        )
    return result.stdout.decode().rstrip("\n")


def get_version_from_package():
    return "v" + importlib.metadata.version("dot.py")


def get_version_from_pyproject():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
        return "v" + data["project"]["version"]


if __name__ == "__main__":
    versions = [
        get_version_from_git(),
        get_version_from_package(),
        get_version_from_pyproject(),
    ]
    assert all(v == versions[0] for v in versions), f"Versions are different: {versions}"
