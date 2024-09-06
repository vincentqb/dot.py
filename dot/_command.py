import os
import re
from pathlib import Path
from string import Template

from ._logger import get_counting_logger


def render_recurse(*, candidate, dry_run, logger, **_):
    """
    Render templates recursively.
    """
    for subcandidate in sorted(candidate.glob("**/*.template")):
        if subcandidate.is_file():
            subrendered = re.sub(".template$", "", str(subcandidate))
            render_single(candidate=subcandidate, rendered=subrendered, dry_run=dry_run, logger=logger)


def render_single(*, candidate, rendered, dry_run, logger, **_):
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


def link(*, rendered, dotfile, dry_run, logger, **_):
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


def unlink(*, rendered, dotfile, dry_run, logger, **_):
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
            for func in commands[command]:
                func(candidate=candidate, rendered=rendered, dotfile=dotfile, dry_run=dry_run, logger=logger)


def dot(command, home, profiles, dry_run, verbose):
    logger = get_counting_logger(verbose)
    run(command, home, profiles, True, logger)  # Dry run first

    if logger.warning.counter > 0:
        logger.error("Error: There were conflicts. Exiting without changing dotfiles.")
        raise SystemExit(1)

    if not dry_run:
        logger = get_counting_logger(0)
        run(command, home, profiles, dry_run, logger)  # Wet run second


commands = {"link": [render_recurse, render_single, link], "unlink": [unlink]}
