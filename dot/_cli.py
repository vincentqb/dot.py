"""
Manage links to dotfiles.
"""

from argparse import ArgumentParser

from dot import dot
from dot.command import COMMAND


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


def dot_from_args():
    dot(**parse_args())
