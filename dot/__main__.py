"""
Manage links to dotfiles.
"""

import sys
from argparse import ArgumentParser

from ._command import commands, dot
from ._utils import standardize


class ColoredArgumentParser(ArgumentParser):
    def print_usage(self, file=None):
        if file is None:
            file = sys.stdout
        self._print_message(standardize(self.format_usage(), "yellow"), file)

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout
        self._print_message(standardize(self.format_help()), file)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, standardize(f"Error: {self.prog}: {message.strip()}", "red") + "\n")


def parse_args(prog):
    parser = ColoredArgumentParser(prog=prog, description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for key, funcs in commands.items():
        subparser = subparsers.add_parser(key, description=funcs[-1].__doc__)
        subparser.add_argument("profiles", nargs="+")
        subparser.add_argument("--home", nargs="?", default="~")
        subparser.add_argument("-v", "--verbose", action="count", default=0)
        subparser.add_argument("-d", "--dry-run", default=False, action="store_true")
        subparser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    return vars(parser.parse_args())


def dot_from_args(*, prog="dot.py"):
    dot(**parse_args(prog))


if __name__ == "__main__":
    dot_from_args(prog="dot")
