import pytest

doc_mapping = {
    "link": "Link dotfiles to files in given profile directories.",
    "unlink": "Unlink dotfiles linked to files in given profile directories.",
}


def test_doc_module():
    from dot import __doc__ as doc

    assert doc.strip() == "Manage links to dotfiles."


@pytest.mark.parametrize("command,doc", doc_mapping.items())
def test_doc_mapping(command, doc):
    from dot import commands

    assert doc == commands[command][-1].__doc__.strip()
