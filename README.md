# dot.py

**dot.py** is a minimalist one-file python script for managing dotfiles via symbolic links. Inspired by [bashdot](https://github.com/bashdot/bashdot), it supports multiple profiles and customizable file templates with variables. Requires **python 3.10+**.

## Example Quick Start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and read `dot.py` help

   ```sh
   uvx --from dot-py dot.py -h
   ```

1. Suppose you have a folder called `~/dotfiles/default/` containing `~/dotfiles/default/config/` and `~/dotfiles/default/netrc.template`, and you want them link as `~/.config` and `~/.netrc`. Suppose also that `~/dotfiles/default/netrc.template` contains

```
machine github.com
login vincentqb
password $GITHUB
```

1. Manually delete existing `~/.netrc` and `~/.config`.

1. Run

   ```sh
    GITHUB=some_api_key uvx --from dot-py dot.py ~/doftiles/default
   ```

1. You now have `~/.netrc` and `~/.config` linked to `~/dotfiles/default/netrc.rendered` and `~/dotfiles/default/config`. Moreover, `~/dotfiles/default/netrc.rendered` contains

```
machine github.com
login vincentqb
password some_api_key
```

## Development

For linting, building and testing, see the [workflow](https://github.com/vincentqb/dot.py/blob/main/.github/workflows/python-app.yml).

![Test](https://github.com/vincentqb/dot.py/actions/workflows/python-app.yml/badge.svg)
