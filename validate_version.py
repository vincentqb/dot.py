#!/usr/bin/env python3

import importlib.metadata
import subprocess

import tomllib


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


versions = [
    get_version_from_git(),
    get_version_from_package(),
    get_version_from_pyproject(),
]
print(versions)

if all(v == versions[0] for v in versions):
    exit(0)

exit(1)
