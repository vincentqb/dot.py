#!/usr/bin/env python3
"""
Manage links to dotfiles.
"""

__all__ = ["dot", "dot_from_args"]

import os
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from collections import Counter
from pathlib import Path
from shutil import copymode
from string import Template


def __dir__():
    return __all__


# --- output -----------------------------------------------------------------

RESET = "\x1b[0m"
STYLES = {
    "info": "\x1b[90m",  # dark gray
    "warning": "\x1b[33m",  # yellow
    "error": "\x1b[31m",  # red
}


def style(msg, level):
    return f"{STYLES[level]}{msg}{RESET}"


class Printer:
    """
    Emit styled messages to stderr and count warnings.

    Info messages show the plan and are only emitted during a dry run;
    warnings and errors are always emitted.
    """

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.warnings = 0

    def info(self, msg):
        if self.dry_run:
            print(style(msg, "info"), file=sys.stderr)

    def warning(self, msg):
        self.warnings += 1
        print(style(msg, "warning"), file=sys.stderr)

    def error(self, msg):
        print(style(msg, "error"), file=sys.stderr)


# --- operations -------------------------------------------------------------


def render(template, rendered, printer, apply):
    """Render a template."""
    if rendered.is_symlink():
        printer.warning(f"File {rendered} exists but is a link.")
        return
    if rendered.is_dir():
        printer.warning(f"File {rendered} exists but is a directory.")
        return
    content = Template(template.read_text(encoding="utf-8")).safe_substitute(os.environ)
    if not rendered.exists():
        printer.info(f"File {rendered} will be created.")
    elif rendered.read_text(encoding="utf-8") != content or rendered.stat().st_mode != template.stat().st_mode:
        printer.info(f"File {rendered} will be updated.")
    else:
        printer.info(f"File {rendered} is up to date.")
        return
    if apply:
        rendered.touch()
        copymode(template, rendered)
        rendered.write_text(content, encoding="utf-8")


def owned(rendered, dotfile, printer):
    if not dotfile.is_symlink():
        printer.warning(f"File {dotfile} exists but is not a link.")
    elif dotfile.resolve() != rendered.resolve():
        printer.warning(f"File {dotfile} exists and points to {dotfile.readlink()} instead of {rendered}.")
    else:
        return True
    return False


def link(rendered, dotfile, printer, apply):
    if not dotfile.exists() and not dotfile.is_symlink():
        printer.info(f"File {dotfile} will be created and linked to {rendered}.")
        if apply:
            dotfile.symlink_to(rendered)
    elif owned(rendered, dotfile, printer):
        printer.info(f"File {dotfile} links to {rendered} as expected.")


def unlink(rendered, dotfile, printer, apply):
    if not dotfile.exists() and not dotfile.is_symlink():
        printer.info(f"File {dotfile} does not exist.")
    elif owned(rendered, dotfile, printer):
        printer.info(f"File {dotfile} will be unlinked from {rendered}.")
        if apply:
            dotfile.unlink()


# --- walk + core ------------------------------------------------------------


def walk(profile, home, prefix, printer):
    """Yield (candidate, rendered, dotfile) for each top-level entry in the profile."""
    for candidate in sorted(profile.glob("*")):
        name = candidate.name
        if name.startswith("."):
            printer.info(f"File {candidate} ignored.")
            continue
        if name.endswith(".rendered") and candidate.is_file():
            continue
        if candidate.is_dir():
            yield candidate, candidate, home / f"{prefix}{name}"
        else:
            base = name.removesuffix(".template")
            rendered = candidate.parent / (base + ".rendered") if name.endswith(".template") else candidate
            dotfile = home / f"{prefix}{base}"
            yield candidate, rendered, dotfile


def nested_templates(folder, recursive, printer):
    """Yield (template, rendered, link) for each template nested inside a directory."""
    for depth in range(1, recursive):
        pattern = "/".join(["*"] * depth) + ".template"
        for tmpl in sorted(folder.glob(pattern)):
            if tmpl.is_file():
                base = tmpl.name.removesuffix(".template")
                if not base:
                    printer.warning(f"Template file {tmpl} yields an empty link name.")
                    continue
                yield tmpl, tmpl.with_name(base + ".rendered"), tmpl.with_name(base)


def link_all(candidate, rendered, dotfile, recursive, printer, apply):
    """Link dotfiles to files in given profile directories."""
    if candidate != rendered:
        render(candidate, rendered, printer, apply)
    link(rendered, dotfile, printer, apply)
    if candidate.is_dir():
        for template, nested, nested_link in nested_templates(candidate, recursive, printer):
            render(template, nested, printer, apply)
            link(nested, nested_link, printer, apply)


def unlink_all(candidate, rendered, dotfile, recursive, printer, apply):
    """Unlink dotfiles linked to files in given profile directories."""
    unlink(rendered, dotfile, printer, apply)


def dot(command, home, profiles, prefix, recursive, dry_run):
    printer = Printer(dry_run=dry_run)
    entries = []

    home = Path(home).expanduser().resolve()
    if not home.is_dir():
        printer.warning(f"Folder {home} does not exist.")
    else:
        for p in profiles:
            profile = Path(p).expanduser().resolve()
            if not profile.is_dir():
                printer.warning(f"Profile {profile} does not exist.")
                continue
            entries.extend(walk(profile, home, prefix, printer))

    for dotfile, count in Counter(dotfile for *_, dotfile in entries).items():
        if count > 1:
            printer.warning(f"More than one profile modifies file {dotfile}.")

    for apply in [False] if dry_run else [False, True]:
        for entry in entries:
            COMMANDS[command](*entry, recursive, printer, apply)
        if printer.warnings:
            printer.error("Error: There were conflicts. Exiting without changing dotfiles.")
            raise SystemExit(1)


# --- CLI --------------------------------------------------------------------

COMMANDS = {
    "link": link_all,
    "unlink": unlink_all,
}


def dot_from_args(*, prog="dot.py"):
    parser = ArgumentParser(prog=prog, description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for cmd, fn in COMMANDS.items():
        sp = subparsers.add_parser(cmd, description=fn.__doc__)
        sp.add_argument("profiles", nargs="+", help="profile directories to process")
        sp.add_argument("--home", default="~", help="directory receiving the dotfiles (default: ~)")
        sp.add_argument("--prefix", "-p", default=".", help="string prepended to each linked file name (default: .)")
        sp.add_argument(
            "-r",
            "--recursive",
            action="count",
            default=1,
            help="increase depth of recursion when rendering templates",
        )
        sp.add_argument(
            "-d", "--dry-run", default=False, action=BooleanOptionalAction, help="show the plan without applying it"
        )
    dot(**vars(parser.parse_args()))


if __name__ == "__main__":
    dot_from_args(prog="dot")
