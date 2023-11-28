from .command import run
from .logger import get_counting_logger

__all__ = ["dot"]


def dot(command, home, profiles, dry_run):
    logger = get_counting_logger(dry_run)
    run(command, home, profiles, True, logger)  # Dry run first

    if logger.warning.counter > 0:
        logger.error("Error: There were conflicts. Exiting without changing dotfiles.")
        raise SystemExit(1)

    if not dry_run:
        run(command, home, profiles, dry_run, logger)  # Wet run second
