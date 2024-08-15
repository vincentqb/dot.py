import importlib

import pytest

doc_mapping = {
    "link": "Link dotfiles to files in given profile directories.",
    "unlink": "Unlink dotfiles linked to files in given profile directories.",
}
doc_func = {("dot._command", k): v for k, v in doc_mapping.items()}


def test_doc_module():
    from dot.__main__ import __doc__ as doc

    assert doc.strip() == "Manage links to dotfiles."


@pytest.mark.parametrize("command,doc", doc_mapping.items())
def test_doc_mapping(command, doc):
    from dot._command import commands

    assert doc == commands[command][-1].__doc__.strip()


@pytest.mark.parametrize("obj,doc", doc_func.items())
def test_doc_func(obj, doc):
    module, func = obj
    module = importlib.import_module(module)
    func = getattr(module, func)
    assert doc == func.__doc__.strip()
