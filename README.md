# dot.py

**dot.py** is a minimalist one-file python script for managing dotfiles via symbolic links. Inspired by [bashdot](https://github.com/bashdot/bashdot), it supports multiple profiles and customizable file templates with variables. No external dependencies, just **python 3.10+**.

## Example Quick Start

1. Download [dot.py](https://raw.githubusercontent.com/vincentqb/dot.py/main/dot.py) to `~/dot.py` and read its help

   ```sh
   python3 ~/dot.py -h
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
   GITHUB=some_api_key python3 ~/dot.py link ~/dotfiles/default
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
