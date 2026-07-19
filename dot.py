#!/usr/bin/env python3
"""
Manage links to dotfiles.
"""

__all__ = ["dot", "dot_from_args"]

import os
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from dataclasses import dataclass
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


# --- actions ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Render:
    """Render a template: read 'source', substitute env vars, write to 'target' with 'source' permissions."""

    source: Path
    target: Path

    def apply(self) -> None:
        content = Template(self.source.read_text(encoding="utf-8")).safe_substitute(os.environ)
        # Copy permissions before writing so a rendered secret is never
        # world-readable, even briefly.
        self.target.touch()
        copymode(self.source, self.target)
        self.target.write_text(content, encoding="utf-8")


@dataclass(frozen=True, slots=True)
class Symlink:
    """Create a symbolic link at 'target' pointing to 'source'."""

    source: Path
    target: Path

    def apply(self) -> None:
        self.target.symlink_to(self.source)


@dataclass(frozen=True, slots=True)
class Unlink:
    """Remove the symlink at 'target'."""

    source: Path
    target: Path

    def apply(self) -> None:
        self.target.unlink()


# --- planners ---------------------------------------------------------------


def plan_render(candidate, rendered, printer):
    """Render a template."""
    if candidate == rendered:
        return None
    if rendered.is_symlink():
        printer.warning(f"File {rendered} exists but is a link")
        return None
    printer.info(f"File {rendered} will be created.")
    return Render(candidate, rendered)


def plan_link(rendered, dotfile, printer):
    # Check is_symlink too: exists() follows links, so a dangling symlink
    # otherwise looks absent and symlink_to would fail on apply.
    if not dotfile.exists() and not dotfile.is_symlink():
        printer.info(f"File {dotfile} will be created and linked to {rendered}")
        return Symlink(rendered, dotfile)
    if not dotfile.is_symlink():
        printer.warning(f"File {dotfile} exists but is not a link")
        return None
    actual = dotfile.readlink()
    if actual != rendered:
        printer.warning(f"File {dotfile} exists and points to {actual} instead of {rendered}")
        return None
    printer.info(f"File {dotfile} links to {rendered} as expected")
    return None


def plan_unlink(rendered, dotfile, printer):
    # Check is_symlink too so a dangling symlink can still be unlinked.
    if not dotfile.exists() and not dotfile.is_symlink():
        printer.warning(f"File {dotfile} does not exist")
        return None
    if not dotfile.is_symlink():
        printer.warning(f"File {dotfile} exists but is not a link")
        return None
    actual = dotfile.readlink()
    if actual != rendered:
        printer.warning(f"File {dotfile} exists and points to {actual} instead of {rendered}")
        return None
    printer.info(f"File {dotfile} will be unlinked from {rendered}")
    return Unlink(rendered, dotfile)


# --- walk + core ------------------------------------------------------------


def walk(profile, home, printer):
    """Yield (candidate, rendered, dotfile) for each top-level entry in the profile."""
    for candidate in sorted(profile.glob("*")):
        name = candidate.name
        if name.startswith(".") or (name.endswith(".rendered") and candidate.is_file()):
            printer.info(f"File {candidate} ignored.")
            continue
        if candidate.is_dir():
            yield candidate, candidate, home / f".{name}"
        else:
            base = name.removesuffix(".template")
            rendered = candidate.parent / (base + ".rendered") if name.endswith(".template") else candidate
            dotfile = home / ("." + base)
            yield candidate, rendered, dotfile


def nested_templates(folder, recursive):
    """Yield (template, rendered, link) for each template nested inside a directory."""
    for depth in range(1, recursive):
        pattern = "/".join(["*"] * depth) + ".template"
        for tmpl in sorted(folder.glob(pattern)):
            # Skip hidden files: a file named exactly ".template" matches
            # "*.template" and would render to an empty name.
            if tmpl.is_file() and not tmpl.name.startswith("."):
                base = tmpl.name.removesuffix(".template")
                yield tmpl, tmpl.with_name(base + ".rendered"), tmpl.with_name(base)


def plan_link_all(candidate, rendered, dotfile, recursive, printer):
    """Link dotfiles to files in given profile directories."""
    out = []
    if a := plan_render(candidate, rendered, printer):
        out.append(a)
    if a := plan_link(rendered, dotfile, printer):
        out.append(a)
    if candidate.is_dir():
        for tsrc, tdst, tlink in nested_templates(candidate, recursive):
            if a := plan_render(tsrc, tdst, printer):
                out.append(a)
            if a := plan_link(tdst, tlink, printer):
                out.append(a)
    return out


def plan_unlink_all(candidate, rendered, dotfile, recursive, printer):
    """Unlink dotfiles linked to files in given profile directories."""
    # Nested rendered files inside directories are intentionally left in place:
    # 'unlink' keeps the profile partially rendered so a subsequent 'link'
    # does not have to re-render.
    out = []
    if a := plan_unlink(rendered, dotfile, printer):
        out.append(a)
    return out


def dot(command, home, profiles, recursive, dry_run):
    printer = Printer(dry_run=dry_run)
    queue = []
    planner = COMMANDS[command]

    home = Path(home).expanduser().resolve()
    if not home.is_dir():
        printer.warning(f"Folder {home} does not exist")
    else:
        for p in profiles:
            profile = Path(p).expanduser().resolve()
            if not profile.is_dir():
                printer.warning(f"Profile {profile} does not exist")
                continue
            for candidate, rendered, dotfile in walk(profile, home, printer):
                queue.extend(planner(candidate, rendered, dotfile, recursive, printer))

    # Catch duplicate profiles and name collisions across profiles: planners
    # check the filesystem, so two actions on one target pass planning but
    # break on apply.
    seen = set()
    for action in queue:
        if action.target in seen:
            printer.warning(f"File {action.target} is planned more than once")
        seen.add(action.target)

    if printer.warnings:
        printer.error("Error: There were conflicts. Exiting without changing dotfiles.")
        raise SystemExit(1)

    if not dry_run:
        for action in queue:
            action.apply()


# --- CLI --------------------------------------------------------------------

COMMANDS = {
    "link": plan_link_all,
    "unlink": plan_unlink_all,
}


def dot_from_args(*, prog="dot.py"):
    parser = ArgumentParser(prog=prog, description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for cmd, fn in COMMANDS.items():
        sp = subparsers.add_parser(cmd, description=fn.__doc__)
        sp.add_argument("profiles", nargs="+")
        sp.add_argument("--home", default="~")
        sp.add_argument(
            "-r",
            "--recursive",
            action="count",
            default=1,
            help="increase depth of recursion when rendering templates",
        )
        sp.add_argument("-d", "--dry-run", default=False, action=BooleanOptionalAction)
    dot(**vars(parser.parse_args()))


if __name__ == "__main__":
    dot_from_args(prog="dot")
