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

## Destination prefix

`--prefix` (`-p`) specifies the complete destination path before each file name. It defaults to `~/.`, so a profile file named `bashrc` links as `~/.bashrc`.

| Option            | Destination for `bashrc`           |
| ----------------- | ---------------------------------- |
| `--prefix /tmp/.` | `/tmp/.bashrc`                     |
| `--prefix /tmp/`  | `/tmp/bashrc`                      |
| `--prefix /tmp/_` | `/tmp/_bashrc`                     |
| `--prefix .`      | `.bashrc` in the current directory |
| `--prefix ""`     | `bashrc` in the current directory  |

The destination directory must already exist. Relative prefixes use the current directory, and `~` expands to your home directory. Use the same prefix for `link` and `unlink`.

For example, `--home /tmp --prefix _` becomes `--prefix /tmp/_`.

Profiles can contain dotted file and directory names. Use `--prefix ~/` to preserve them: `.bashrc` links as `~/.bashrc`, and `.config` links as `~/.config`. Prefixes are literal, so `--prefix ~/.` would add another dot to those names.

The `.git` entry and generated `*.rendered` files are excluded. Template names must contain a file name before the `.template` suffix.

## Development

For linting, building and testing, see the [workflow](https://github.com/vincentqb/dot.py/blob/main/.github/workflows/python-app.yml).

![Test](https://github.com/vincentqb/dot.py/actions/workflows/python-app.yml/badge.svg)
