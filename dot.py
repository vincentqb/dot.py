#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "rich",
#     "typer",
# ]
# ///
"""
Manage links to dotfiles.
"""

__all__ = ["dot", "dot_from_args"]

import os
from dataclasses import dataclass
from pathlib import Path
from shutil import copymode
from string import Template
from typing import Annotated

import typer
from rich.console import Console


def __dir__():
    return __all__


# --- output -----------------------------------------------------------------

console = Console(stderr=True, highlight=False, markup=False, soft_wrap=True)


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
            console.print(msg, style="bright_black")

    def warning(self, msg):
        self.warnings += 1
        console.print(msg, style="yellow")

    def error(self, msg):
        console.print(msg, style="red")


# --- actions ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Render:
    """Render a template: read 'source', substitute env vars, write to 'target' with 'source' permissions."""

    source: Path
    target: Path

    def apply(self) -> None:
        content = Template(self.source.read_text(encoding="utf-8")).safe_substitute(os.environ)
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

app = typer.Typer(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})

Profiles = Annotated[list[Path], typer.Argument(help="profile directories to process")]
Home = Annotated[Path, typer.Option(help="directory receiving the dotfiles")]
Recursive = Annotated[
    int, typer.Option("--recursive", "-r", count=True, help="increase depth of recursion when rendering templates")
]
DryRun = Annotated[bool, typer.Option("--dry-run/--no-dry-run", "-d", help="show the plan without applying it")]


@app.command(help=plan_link_all.__doc__)
def link(profiles: Profiles, home: Home = Path("~"), recursive: Recursive = 0, dry_run: DryRun = False):
    dot("link", home, profiles, recursive + 1, dry_run)


@app.command(help=plan_unlink_all.__doc__)
def unlink(profiles: Profiles, home: Home = Path("~"), recursive: Recursive = 0, dry_run: DryRun = False):
    dot("unlink", home, profiles, recursive + 1, dry_run)


def dot_from_args(*, prog="dot.py"):
    app(prog_name=prog)


if __name__ == "__main__":
    dot_from_args(prog="dot")
