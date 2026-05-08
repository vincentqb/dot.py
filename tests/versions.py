#!/usr/bin/env python3

import importlib.metadata
import subprocess

import tomllib


def get_version_from_git():
    cmd = "git describe --tags --abbrev=0".split()
    result = subprocess.run(cmd, capture_output=True, check=True)
    return result.stdout.decode().rstrip("\n")


def get_version_from_package():
    return "v" + importlib.metadata.version("dot.py")


def get_version_from_pyproject():
    with open("pyproject.toml", "rb") as f:
        return "v" + tomllib.load(f)["project"]["version"]


if __name__ == "__main__":
    versions = [
        get_version_from_git(),
        get_version_from_package(),
        get_version_from_pyproject(),
    ]
    if len(set(versions)) != 1:
        raise SystemExit(f"Versions are different: {versions}")
