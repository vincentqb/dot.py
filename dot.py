#!/usr/bin/env python3
"""
Manage links to dotfiles.
"""

__all__: list[str] = ["dot"]
__ALL__: list[str] = dir() + __all__

import logging
import os
import re
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from string import Template
from typing import Callable


def __dir__() -> list[str]:
    return __ALL__


class ColoredFormatter(logging.Formatter):
    COLORS: dict[str, str] = {
        "blue": "\x1b[36;20m",
        "green": "\x1b[32;20m",
        "grey": "\x1b[38;20m",
        "red": "\x1b[31;20m",
        "red bold": "\x1b[31;1m",
        "reset": "\x1b[0m",
        "yellow": "\x1b[33;20m",
    }

    LEVELS_TO_COLOR: dict[int, str] = {
        logging.DEBUG: "grey",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "red bold",
    }

    def format_(self, msg, levelno) -> str:
        color = self.LEVELS_TO_COLOR.get(levelno, "reset")
        color = self.COLORS[color]
        # Apply color and capitalize the first word of each line
        return (
            color
            + "\n".join((m[0].upper() if len(m) > 0 else "") + (m[1:] if len(m) > 1 else "") for m in msg.split("\n"))
            + self.COLORS["reset"]
        )

    def format(self, record: logging.LogRecord) -> str:
        record.msg = self.format_(record.msg, record.levelno)
        return logging.Formatter().format(record)


def get_logger() -> logging.Logger:
    logger = logging.getLogger()

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def render_link_recurse(*, candidate, recursive, queue, **_) -> None:
    """
    Render templates recursively.
    """
    # TODO only templates in root, n-deep recursing, or any-deep recursing
    # templates = sorted(candidate.glob("*.template"))
    templates = sorted(sum([list(candidate.glob("/".join("*" * r) + ".template")) for r in range(recursive)], []))
    # templates = sorted(candidate.glob("**/*.template"))
    for subcandidate in templates:
        if subcandidate.is_file():
            # NOTE file.template -> file.rendered -> file
            subname = subcandidate.name
            subrendered = subcandidate.parent / re.sub(".template$", ".rendered", subname)
            subdotfile = subcandidate.parent / re.sub(".template$", "", subname)
            render_single(candidate=subcandidate, rendered=subrendered, queue=queue)
            link(rendered=subrendered, dotfile=subdotfile, queue=queue)


def render_single(*, candidate, rendered, queue, **_) -> None:
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
        logger.info(f"File {rendered} created.")


def link(*, rendered, dotfile, queue, **_):
    """
    Link dotfiles to files in given profile directories.
    """
    if not dotfile.exists():

        def func():
            dotfile.symlink_to(rendered)

        queue.append(func)
        return logger.info(f"File {dotfile} created and linked to {rendered}")

    if not dotfile.is_symlink():
        return logger.warning(f"File {dotfile} exists but is not a link")

    dotfile_link = dotfile.readlink()
    if dotfile_link != rendered:
        return logger.warning(f"File {dotfile} exists and points to {dotfile_link} instead of {rendered}")

    return logger.info(f"File {dotfile} links to {rendered} as expected")


def unlink(*, rendered, dotfile, queue, **_):
    """
    Unlink dotfiles linked to files in given profile directories.
    """
    if not dotfile.exists():
        return logger.warning(f"File {dotfile} does not exists")

    if not dotfile.is_symlink():
        return logger.warning(f"File {dotfile} exists but is not a link")

    dotfile_link = dotfile.readlink()
    if dotfile_link != rendered:
        return logger.warning(f"File {dotfile} exists and points to {dotfile_link} instead of {rendered}")

    def func():
        dotfile.unlink()

    queue.append(func)
    return logger.info(f"File {dotfile} unlinked from {rendered}")


def run(command, home, profiles, recursive, queue):
    home = Path(home).expanduser().resolve()
    if not home.is_dir():
        return logger.warning(f"Folder {home} does not exist")
    for profile in profiles:
        profile = Path(profile).expanduser().resolve()
        if not profile.is_dir():
            logger.warning(f"Profile {profile} does not exist")
            continue
        for candidate in sorted(profile.glob("*")):
            name = candidate.name
            if name.startswith(".") or (name.endswith(".rendered") and candidate.is_file()):
                logger.debug(f"File {candidate} ignored.")
                continue
            # Add dot prefix and replace template when needed
            if candidate.is_dir():
                rendered = candidate
                dotfile = home / ("." + name)
            else:
                # NOTE file.template -> file.rendered -> .file
                rendered = candidate.parent / re.sub(".template$", ".rendered", name)
                dotfile = home / ("." + re.sub(".template$", "", name))
            # Run user requested command
            for func in commands[command]:
                func(
                    candidate=candidate,
                    rendered=rendered,
                    dotfile=dotfile,
                    recursive=recursive,
                    queue=queue,
                )


class AddWarningTrackerHandlerContext:
    def __init__(self):
        class WarningTrackerHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.warning_called = False

            def emit(self, record):
                if record.levelno == logging.WARNING:
                    self.warning_called = True

        self.handler = WarningTrackerHandler()

    def __enter__(self):
        logger.addHandler(self.handler)
        return self.handler

    def __exit__(self, exc_type, exc_value, traceback):
        logger.removeHandler(self.handler)


def dot(command, home, profiles, recursive, dry_run, verbose) -> None:
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logger.setLevel(level)

    # Build queue
    queue = []

    with AddWarningTrackerHandlerContext():
        run(command, home, profiles, recursive=recursive, queue=queue)

        if logger.handlers[-1].warning_called:
            logger.error("Error: There were conflicts. Exiting without changing dotfiles.")
            raise SystemExit(1)

    # Execute queue
    if not dry_run:
        for func in queue:
            func()


def dot_from_args(*, prog: str = "dot.py") -> None:
    def parse_args(prog):
        class ColoredArgumentParser(ArgumentParser):
            def print_usage(self, file=None):
                if file is None:
                    file = sys.stdout
                self._print_message(formatter.format_(self.format_usage(), logging.WARNING), file)

            def print_help(self, file=None):
                if file is None:
                    file = sys.stdout
                self._print_message(formatter.format_(self.format_help(), logging.DEBUG), file)

            def error(self, message):
                self.print_usage(sys.stderr)
                self.exit(2, formatter.format_(f"Error: {self.prog}: {message.strip()}", logging.ERROR) + "\n")

        parser = ColoredArgumentParser(prog=prog, description=__doc__)
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


formatter: ColoredFormatter = ColoredFormatter()
logger: logging.Logger = get_logger()
commands: dict[str, list[Callable]] = {"link": [render_link_recurse, render_single, link], "unlink": [unlink]}


if __name__ == "__main__":
    dot_from_args(prog="dot")
