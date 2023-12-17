import importlib

import pytest

doc_func = {
    ("dot.command", "link"): "Link dotfiles to files in given profile directories.",
    ("dot.command", "unlink"): "Unlink dotfiles linked to files in given profile directories.",
}


def test_doc_module():
    from dot.__main__ import __doc__ as doc

    assert doc.strip() == "Manage links to dotfiles."


@pytest.mark.parametrize("obj,doc", doc_func.items())
def test_doc_func(obj, doc):
    module, func = obj
    module = importlib.import_module(module)
    func = getattr(module, func)
    assert doc == func.__doc__.strip()
