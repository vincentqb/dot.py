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
from string import Template


def __dir__():
    return __all__


# --- output -----------------------------------------------------------------

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

    Thresholds:
        verbose=True        -> debug (show everything)
        dry_run=True only   -> info  (show the plan)
        neither             -> warning (quiet success)
    """

    def __init__(self, verbose=False, dry_run=False):
        if verbose:
            level = "debug"
        elif dry_run:
            level = "info"
        else:
            level = "warning"
        self.threshold = _RANK[level]
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


# --- actions ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Render:
    """Render a template: read 'source', substitute env vars, write to 'target'."""

    source: Path
    target: Path

    def apply(self) -> None:
        content = Template(self.source.read_text(encoding="utf-8")).safe_substitute(os.environ)
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
    """Remove the symlink at 'target'. 'source' is retained for context."""

    source: Path
    target: Path

    def apply(self) -> None:
        self.target.unlink()


# --- planners ---------------------------------------------------------------


def _plan_render(candidate, rendered, printer):
    """Render a template."""
    if candidate == rendered:
        return None
    printer.info(f"File {rendered} created.")
    return Render(candidate, rendered)


def _plan_link(rendered, dotfile, printer):
    """Link dotfiles to files in given profile directories."""
    if not dotfile.exists():
        printer.info(f"File {dotfile} created and linked to {rendered}")
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


def _plan_unlink(rendered, dotfile, printer):
    """Unlink dotfiles linked to files in given profile directories."""
    if not dotfile.exists():
        printer.warning(f"File {dotfile} does not exist")
        return None
    if not dotfile.is_symlink():
        printer.warning(f"File {dotfile} exists but is not a link")
        return None
    actual = dotfile.readlink()
    if actual != rendered:
        printer.warning(f"File {dotfile} exists and points to {actual} instead of {rendered}")
        return None
    printer.info(f"File {dotfile} unlinked from {rendered}")
    return Unlink(rendered, dotfile)


# --- walk + core ------------------------------------------------------------


def _walk(profile, home, printer):
    """Yield (candidate, rendered, dotfile) for each top-level entry in the profile."""
    for candidate in sorted(profile.glob("*")):
        name = candidate.name
        if name.startswith(".") or (name.endswith(".rendered") and candidate.is_file()):
            printer.debug(f"File {candidate} ignored.")
            continue
        if candidate.is_dir():
            yield candidate, candidate, home / f".{name}"
        else:
            base = name.removesuffix(".template")
            rendered = candidate.parent / (base + ".rendered") if name.endswith(".template") else candidate
            dotfile = home / ("." + base)
            yield candidate, rendered, dotfile


def _nested_templates(folder, recursive):
    """Yield (template, rendered, link) for each template nested inside a directory."""
    for depth in range(recursive):
        pattern = "/".join(["*"] * depth) + ".template" if depth else ".template"
        for tmpl in sorted(folder.glob(pattern)):
            if tmpl.is_file():
                base = tmpl.name.removesuffix(".template")
                yield tmpl, tmpl.with_name(base + ".rendered"), tmpl.with_name(base)


def _plan_link_all(candidate, rendered, dotfile, recursive, printer):
    """Queue render + symlink actions for one top-level entry, plus any nested templates."""
    out = []
    if a := _plan_render(candidate, rendered, printer):
        out.append(a)
    if a := _plan_link(rendered, dotfile, printer):
        out.append(a)
    if candidate.is_dir():
        for tsrc, tdst, tlink in _nested_templates(candidate, recursive):
            if a := _plan_render(tsrc, tdst, printer):
                out.append(a)
            if a := _plan_link(tdst, tlink, printer):
                out.append(a)
    return out


def dot(command, home, profiles, recursive, dry_run, verbose):
    printer = Printer(verbose=verbose, dry_run=dry_run)
    queue = []

    home = Path(home).expanduser().resolve()
    if not home.is_dir():
        printer.warning(f"Folder {home} does not exist")
    else:
        for p in profiles:
            profile = Path(p).expanduser().resolve()
            if not profile.is_dir():
                printer.warning(f"Profile {profile} does not exist")
                continue
            for candidate, rendered, dotfile in _walk(profile, home, printer):
                if command == "link":
                    # Nested templates inside directories are rendered and
                    # linked in-place. Intentionally not unlinked: 'unlink'
                    # leaves the profile partially rendered so a subsequent
                    # 'link' does not have to re-render.
                    queue.extend(_plan_link_all(candidate, rendered, dotfile, recursive, printer))
                elif a := _plan_unlink(rendered, dotfile, printer):
                    queue.append(a)

    if printer.warnings:
        printer.error("Error: There were conflicts. Exiting without changing dotfiles.")
        raise SystemExit(1)

    if not dry_run:
        for action in queue:
            action.apply()


# --- CLI --------------------------------------------------------------------

_COMMANDS = {
    "link": _plan_link,
    "unlink": _plan_unlink,
}


def dot_from_args(*, prog="dot.py"):
    parser = ArgumentParser(prog=prog, description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for cmd, fn in _COMMANDS.items():
        sp = subparsers.add_parser(cmd, description=fn.__doc__)
        sp.add_argument("profiles", nargs="+")
        sp.add_argument("--home", nargs="?", default="~")
        sp.add_argument(
            "-r",
            "--recursive",
            action="count",
            default=1,
            help="increase depth of recursion when rendering templates",
        )
        sp.add_argument("-v", "--verbose", action="store_true")
        sp.add_argument("-d", "--dry-run", default=False, action=BooleanOptionalAction)
    dot(**vars(parser.parse_args()))


if __name__ == "__main__":
    dot_from_args(prog="dot")
