#!/usr/bin/env python3

from importlib.metadata import version
from subprocess import run


def get_version_from_git():
    cmd = "git describe --tags --abbrev=0".split()
    result = run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("could not get version from git")
    return result.stdout.decode().rstrip("\n")


def get_version_from_md():
    return "v" + version("dot.py")


vgit = get_version_from_git()
vmd = get_version_from_md()
if vgit == vmd:
    exit(0)

exit(1)
