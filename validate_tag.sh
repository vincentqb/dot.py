#!/bin/bash

# version from pyproject
a=$(python -c "import importlib.metadata; print(f'v{importlib.metadata.version('dot.py')}')")
# version from git tag
b=$(git describe --tags --abbrev=0)

[ $a = $b ]
exit "$?"
