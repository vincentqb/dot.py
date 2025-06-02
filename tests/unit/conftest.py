import pytest
from pathlib import Path


@pytest.fixture
def root(tmp_path):
    root = Path(str(tmp_path))
    home = root / "home"
    home.mkdir(parents=True)
    yield root
