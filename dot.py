#!/usr/bin/env python3
"""
Manage links to dotfiles.
"""

import logging
import os
import re
from argparse import ArgumentParser
from pathlib import Path
from string import Template

__all__ = ["dot"]


def get_env(key):
    return os.environ.get(key, "false").lower() in ("true", "t", "1")


def get_counting_logger(dry_run):
    class ColoredFormatter(logging.Formatter):
        GREY = "\x1b[38;20m"
        YELLOW = "\x1b[33;20m"
        RED = "\x1b[31;20m"
        BOLD_RED = "\x1b[31;1m"
        RESET = "\x1b[0m"
        FORMAT = "%(message)s"
        formats = {
            logging.DEBUG: GREY + FORMAT + RESET,
            logging.INFO: GREY + FORMAT + RESET,
            logging.WARNING: YELLOW + FORMAT + RESET,
            logging.ERROR: RED + FORMAT + RESET,
            logging.CRITICAL: BOLD_RED + FORMAT + RESET,
        }

        def format(self, record):
            format_ = self.formats.get(record.levelno)
            return logging.Formatter(format_).format(record)

    level = logging.WARNING
    if get_env("DOT_DEBUG"):
        level = logging.DEBUG
    elif dry_run:
        level = logging.INFO

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(ColoredFormatter())

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)

    class CallCounter:
        def __init__(self, method):
            self.method = method
            self.counter = 0

        def __call__(self, *args, **kwargs):
            self.counter += 1
            return self.method(*args, **kwargs)

    logger.warning = CallCounter(logger.warning)
    return logger


def render_recurse(candidate, rendered, _, dry_run, logger):
    """
    Render templates recursively.
    """
    if get_env("DOT_RR"):
        for subcandidate in sorted(candidate.glob("**/*.template")):
            if subcandidate.is_file():
                subrendered = re.sub(".template$", "", str(subcandidate))
                render_single(subcandidate, subrendered, _, dry_run, logger)


def render_single(candidate, rendered, _, dry_run, logger):
    """
    Render a template.
    """
    if candidate != rendered:
        if not dry_run:
            with open(candidate, "r", encoding="utf-8") as candidate_file:
                with open(rendered, "w", encoding="utf-8") as rendered_file:
                    content = Template(candidate_file.read()).safe_substitute(os.environ)
                    rendered_file.write(content)
        logger.info(f"File {rendered} created.")


def link(_, rendered, dotfile, dry_run, logger):
    """
    Link dotfiles to files in given profile directories.
    """
    if not dotfile.exists():
        if not dry_run:
            dotfile.symlink_to(rendered)
        return logger.info(f"File {dotfile} created and linked to {rendered}")

    if not dotfile.is_symlink():
        return logger.warning(f"File {dotfile} exists but is not a link")

    dotfile_link = Path(os.readlink(str(dotfile))).expanduser().resolve()
    if dotfile_link != rendered:
        return logger.warning(f"File {dotfile} exists and points to {dotfile_link} instead of {rendered}")

    return logger.info(f"File {dotfile} links to {rendered} as expected")


def unlink(_, rendered, dotfile, dry_run, logger):
    """
    Unlink dotfiles linked to files in given profile directories.
    """
    if not dotfile.exists():
        return logger.warning(f"File {dotfile} does not exists")

    if not dotfile.is_symlink():
        return logger.warning(f"File {dotfile} exists but is not a link")

    dotfile_link = Path(os.readlink(str(dotfile))).expanduser().resolve()
    if dotfile_link != rendered:
        return logger.warning(f"File {dotfile} exists and points to {dotfile_link} instead of {rendered}")

    if not dry_run:
        dotfile.unlink()
    return logger.info(f"File {dotfile} unlinked from {rendered}")


def run(command, home, profiles, dry_run, logger):
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
                rendered = candidate.parent / re.sub(".template$", ".rendered", name)
                dotfile = home / ("." + re.sub(".template$", "", name))
            # Run user requested command
            for func in COMMAND[command]:
                func(candidate, rendered, dotfile, dry_run, logger)


def dot(command, home, profiles, dry_run):
    logger = get_counting_logger(dry_run)
    run(command, home, profiles, True, logger)  # Dry run first

    if logger.warning.counter > 0:
        logger.error("There were conflicts: exiting without changing dotfiles.")
        raise SystemExit(1)

    if not dry_run:
        run(command, home, profiles, dry_run, logger)  # Wet run second


def dot_from_args():
    def parse_args():
        parser = ArgumentParser(description=__doc__)
        subparsers = parser.add_subparsers(dest="command", required=True)
        for key, funcs in COMMAND.items():
            subparser = subparsers.add_parser(key, description=funcs[-1].__doc__)
            subparser.add_argument("profiles", nargs="+")
            subparser.add_argument("--home", nargs="?", default="~")
            subparser.add_argument("-d", "--dry-run", default=False, action="store_true")
            subparser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
        return vars(parser.parse_args())

    dot(**parse_args())


COMMAND = {"link": [render_recurse, render_single, link], "unlink": [unlink]}
if __name__ == "__main__":
    dot_from_args()
