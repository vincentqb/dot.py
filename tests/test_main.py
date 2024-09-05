import pytest
from conftest import set_env

from dot import dot


@pytest.mark.parametrize("command", ["link", "unlink"])
@pytest.mark.parametrize("home_folder", ["home", "not_a_home"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_system_exit(root, command, home_folder, dry_run, caplog):
    home = root / home_folder
    profile = root / "not_a_profile"

    with pytest.raises(SystemExit):
        dot(
            command=command,
            home=str(home),
            profiles=[str(profile)],
            render_recursively=False,
            dry_run=dry_run,
            verbose=0,
        )

    assert len(caplog.records) == 2  # TODO may wish to also show profile warnings
    assert home.is_dir() != (home_folder != "home")
    assert not profile.is_dir()


def test_link_unlink_profile(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "bashrc"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=True, verbose=0)
    assert not (home / ".bashrc").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=False, verbose=0)
    assert (home / ".bashrc").is_symlink()

    dot(command="unlink", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=True, verbose=0)
    assert (home / ".bashrc").is_symlink()

    dot(command="unlink", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=False, verbose=0)
    assert not (home / ".bashrc").is_symlink()


@pytest.mark.parametrize("render_recursively", [False, True])
def test_link_unlink_template_recursive(root, render_recursively):
    home = root / "home"
    profile = root / "default"
    target = home / ".folder"
    candidate = profile / "folder" / "env.template"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        dot(
            command="link",
            home=str(home),
            profiles=[str(profile)],
            render_recursively=render_recursively,
            dry_run=True,
            verbose=0,
        )
        assert not (candidate.parent / "env").exists()
        assert not (target / "env").exists()

        dot(
            command="link",
            home=str(home),
            profiles=[str(profile)],
            render_recursively=render_recursively,
            dry_run=False,
            verbose=0,
        )
        assert (not render_recursively) != (candidate.parent / "env").exists()
        assert (not render_recursively) != (target / "env").exists()

    if render_recursively:
        with open(target / "env", "r") as fp:
            assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(
        command="unlink",
        home=str(home),
        profiles=[str(profile)],
        render_recursively=render_recursively,
        dry_run=True,
        verbose=0,
    )
    assert (not render_recursively) != (candidate.parent / "env").exists()
    assert (not render_recursively) != (target / "env").exists()

    if render_recursively:
        with open(target / "env", "r") as fp:
            assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(
        command="unlink",
        home=str(home),
        profiles=[str(profile)],
        render_recursively=render_recursively,
        dry_run=False,
        verbose=0,
    )
    assert (not render_recursively) != (candidate.parent / "env").exists()
    assert not (target / "env").exists()


def test_link_unlink_template(root):
    home = target = root / "home"
    profile = root / "default"
    candidate = profile / "env.template"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("export APP_SECRET_KEY=$APP_SECRET_KEY")

    with set_env(APP_SECRET_KEY="abc123"):
        dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=True, verbose=0)
        assert not (profile / "env.rendered").exists()
        assert not (target / ".env.rendered").exists()
        assert not (target / ".env").is_symlink()

        dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=False, verbose=0)
        assert (profile / "env.rendered").exists()
        assert not (target / ".env.rendered").exists()
        assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=True, verbose=0)
    assert (profile / "env.rendered").exists()
    assert not (target / ".env.rendered").exists()
    assert (target / ".env").is_symlink()

    with open(target / ".env", "r") as fp:
        assert fp.read() == "export APP_SECRET_KEY=abc123"

    dot(command="unlink", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=False, verbose=0)
    assert (profile / "env.rendered").exists()
    assert not (target / ".env.rendered").exists()
    assert not (target / ".env").is_symlink()


def test_link_rendered_folder(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.rendered" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=True, verbose=0)
    assert not (home / ".folder.rendered").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=False, verbose=0)
    assert (home / ".folder.rendered").is_symlink()


def test_link_template_folder(root):
    home = root / "home"
    profile = root / "default"
    candidate = profile / "folder.template" / "config"

    candidate.parent.mkdir(parents=True)
    with open(candidate, "w") as fp:
        fp.write("set -o vi")

    dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=True, verbose=0)
    assert not (profile / "folder.rendered").exists()
    assert not (home / ".folder.template").is_symlink()

    dot(command="link", home=str(home), profiles=[str(profile)], render_recursively=False, dry_run=False, verbose=0)
    assert not (profile / "folder.rendered").exists()
    assert (home / ".folder.template").is_symlink()
