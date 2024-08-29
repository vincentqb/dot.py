import sys

# Workaround for name of cli to be same as name of module
sys.path.pop(0)
from dot.__main__ import dot_from_args

__all__ = ["dot_from_args"]
