import importlib

import pytest

modules = {
    "dot": ["dot"],
}


@pytest.mark.parametrize("module,content", modules.items())
def test_import(module, content):
    module = importlib.import_module(module)
    submodules = [m for m in dir(module) if not m.startswith("_")]
    assert sorted(content) == sorted(submodules)
