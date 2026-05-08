#!/usr/bin/env python3
"""
Manage links to dotfiles.
"""

__all__ = ["dot"]
__ALL__ = dir() + __all__

import os
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from string import Template


def __dir__():
    return __ALL__


_RESET = "\x1b[0m"
_STYLES = {
    "debug": "\x1b[38;20m",  # grey
    "info": "\x1b[32;20m",  # green
    "warning": "\x1b[33;20m",  # yellow
    "error": "\x1b[31;20m",  # red
}
_RANK = {"debug": 0, "info": 1, "warning": 2, "error": 3}


def _style(msg, level):
    color = _STYLES.get(level, "")
    lines = (ln[:1].upper() + ln[1:] for ln in msg.split("\n"))
    return f"{color}{chr(10).join(lines)}{_RESET}"


class Printer:
    """
    Emit styled messages to stderr and count warnings.

    verbose=0 -> warning threshold (quiet success)
    verbose=1 -> info threshold
    verbose>=2 -> debug threshold
    """

    def __init__(self, verbose=0):
        self.threshold = max(_RANK["debug"], _RANK["warning"] - verbose)
        self.warnings = 0

    def _emit(self, level, msg):
        if _RANK[level] < self.threshold:
            return
        print(_style(msg, level), file=sys.stderr)

    def debug(self, msg):
        self._emit("debug", msg)

    def info(self, msg):
        self._emit("info", msg)

    def warning(self, msg):
        self.warnings += 1
        self._emit("warning", msg)

    def error(self, msg):
        self._emit("error", msg)


def render_link_recurse(*, candidate, recursive, queue, printer, **_):
    """
    Render templates recursively.
    """
    # TODO only templates in root, n-deep recursing, or any-deep recursing
    templates = sorted(sum([list(candidate.glob("/".join("*" * r) + ".template")) for r in range(recursive)], []))
    for subcandidate in templates:
        if subcandidate.is_file():
            # NOTE file.template -> file.rendered -> file
            base = subcandidate.name.removesuffix(".template")
            subrendered = subcandidate.parent / (base + ".rendered")
            subdotfile = subcandidate.parent / base
            render_single(candidate=subcandidate, rendered=subrendered, queue=queue, printer=printer)
            link(rendered=subrendered, dotfile=subdotfile, queue=queue, printer=printer)


def render_single(*, candidate, rendered, queue, printer, **_):
    """
    Render a template.
    """

    if candidate != rendered:

        def func():
            with open(candidate, "r", encoding="utf-8") as candidate_file:
                with open(rendered, "w", encoding="utf-8") as rendered_file:
                    content = Template(candidate_file.read()).safe_substitute(os.environ)
                    rendered_file.write(content)

        queue.append(func)
        printer.info(f"File {rendered} created.")


def link(*, rendered, dotfile, queue, printer, **_):
    """
    Link dotfiles to files in given profile directories.
    """
    if not dotfile.exists():

        def func():
            dotfile.symlink_to(rendered)

        queue.append(func)
        printer.info(f"File {dotfile} created and linked to {rendered}")
        return

    if not dotfile.is_symlink():
        printer.warning(f"File {dotfile} exists but is not a link")
        return

    dotfile_link = dotfile.readlink()
    if dotfile_link != rendered:
        printer.warning(f"File {dotfile} exists and points to {dotfile_link} instead of {rendered}")
        return

    printer.info(f"File {dotfile} links to {rendered} as expected")


def unlink(*, rendered, dotfile, queue, printer, **_):
    """
    Unlink dotfiles linked to files in given profile directories.
    """
    if not dotfile.exists():
        printer.warning(f"File {dotfile} does not exist")
        return

    if not dotfile.is_symlink():
        printer.warning(f"File {dotfile} exists but is not a link")
        return

    dotfile_link = dotfile.readlink()
    if dotfile_link != rendered:
        printer.warning(f"File {dotfile} exists and points to {dotfile_link} instead of {rendered}")
        return

    def func():
        dotfile.unlink()

    queue.append(func)
    printer.info(f"File {dotfile} unlinked from {rendered}")


def run(command, home, profiles, recursive, queue, printer):
    home = Path(home).expanduser().resolve()
    if not home.is_dir():
        printer.warning(f"Folder {home} does not exist")
        return
    for profile in profiles:
        profile = Path(profile).expanduser().resolve()
        if not profile.is_dir():
            printer.warning(f"Profile {profile} does not exist")
            continue
        for candidate in sorted(profile.glob("*")):
            name = candidate.name
            if name.startswith(".") or (name.endswith(".rendered") and candidate.is_file()):
                printer.debug(f"File {candidate} ignored.")
                continue
            # Add dot prefix and replace template when needed
            if candidate.is_dir():
                rendered = candidate
                dotfile = home / ("." + name)
            else:
                # NOTE file.template -> file.rendered -> .file
                base = name.removesuffix(".template")
                rendered = candidate.parent / (base + ".rendered") if name.endswith(".template") else candidate
                dotfile = home / ("." + base)
            # Run user requested command
            for func in commands[command]:
                func(
                    candidate=candidate,
                    rendered=rendered,
                    dotfile=dotfile,
                    recursive=recursive,
                    queue=queue,
                    printer=printer,
                )


def dot(command, home, profiles, recursive, dry_run, verbose):
    printer = Printer(verbose=verbose)
    queue = []

    run(command, home, profiles, recursive=recursive, queue=queue, printer=printer)

    if printer.warnings:
        printer.error("Error: There were conflicts. Exiting without changing dotfiles.")
        raise SystemExit(1)

    if not dry_run:
        for func in queue:
            func()


def dot_from_args(*, prog="dot.py"):
    def parse_args(prog):
        parser = ArgumentParser(prog=prog, description=__doc__)
        subparsers = parser.add_subparsers(dest="command", required=True)
        for key, funcs in commands.items():
            subparser = subparsers.add_parser(key, description=funcs[-1].__doc__)
            subparser.add_argument("profiles", nargs="+")
            subparser.add_argument("--home", nargs="?", default="~")
            subparser.add_argument(
                "-r",
                "--recursive",
                action="count",
                default=1,
                help="increase depth of recursion when rendering templates",
            )
            subparser.add_argument("-v", "--verbose", action="count", default=0)
            subparser.add_argument("-d", "--dry-run", default=False, action=BooleanOptionalAction)
        return vars(parser.parse_args())

    dot(**parse_args(prog))


commands = {"link": [render_link_recurse, render_single, link], "unlink": [unlink]}


if __name__ == "__main__":
    dot_from_args(prog="dot")
