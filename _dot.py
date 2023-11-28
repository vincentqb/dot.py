import sys

# Workaround for dot.py cli to import dot package
sys.path.pop(0)
from dot.__main__ import dot_from_args  # noqa
