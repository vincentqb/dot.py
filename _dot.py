import sys

# Workaround to let python build command line called dot.py able to import dot
sys.path.pop(0)
from dot import dot_from_args  # noqa
