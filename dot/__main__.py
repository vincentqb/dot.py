"""
Manage links to dotfiles.
"""

import sys
from argparse import ArgumentParser

from dot import dot
from dot.command import COMMAND
from dot.utils import RED, RESET, YELLOW


class ColoredArgumentParser(ArgumentParser):
    def print_usage(self, file=None):
        if file is None:
            file = sys.stdout
        self._print_message(self.format_usage(), file, YELLOW)

    def _print_message(self, message, file=None, color=None):
        if message:
            if color is None:
                message = message.strip() + "\n"
            else:
                message = color + message.strip() + RESET + "\n"
        super()._print_message(message, file)

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr, RED)
        sys.exit(status)


def parse_args():
    parser = ColoredArgumentParser(description=__doc__)
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


if __name__ == "__main__":
    dot_from_args()
