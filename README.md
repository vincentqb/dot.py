# dotpy

**dotpy** is a minimalist python script for managing dotfiles via symbolic links. Inspired by [bashdot](https://github.com/bashdot/bashdot), it supports multiple profiles and customizable file templates with variables. No external dependencies, just **python 3.6+**.

## Install and Help

You can simply run directly from the repository:

```sh
git clone https://github.com/vincentqb/dotpy ~/dotpy
~/dotpy/dotpy --help
```

or run as module from the repository:

```sh
git clone https://github.com/vincentqb/dotpy ~/dotpy
PYTHONPATH=~/dotpy/ python -m dot --help
```

or build and install from source:

```sh
pip install git+https://github.com/vincentqb/dotpy
dotpy --help
```

or install with pip from pypi:

```sh
pip install dot.py
dotpy --help
```

and just make sure to use the corresponding command below.

## Quick Start

1. Create your initial profile. For example, we create a directory called `default`.

    ```sh
    mkdir default
    ```

1. Add any files you would like linked into your home when this profile is linked.

    ```sh
    echo 'set -o vi' > default/env
    ```

1. Link the profile. When you link, dotpy prepends a dot, in front of the original file name, to the linked file. Below, `default/env` will be linked to `~/.env`.

    ```sh
    ~/dotpy/dotpy link default
    ```

1. Continue adding your dotfiles to the default profile.

   ```sh
   mv ~/.bashrc default/bashrc
   ```

1. You can safely re-run the link command to link newly added files. Store this profile in a cloud drive or source control. Repeat for additional profiles.

## Templates

Values which need to be set in a file when dotpy is run can be placed in a template.

1. Append `.template` to any files which should be rendered. For example, assume you have a file `default/env.template` containing:

    ```sh
    export SECRET_KEY=$ENV_SECRET_KEY
    ```

1. The rendered files will be created in the same directory, and have `.template` replaced with `.rendered`. In the example, you can run the following to set the value `ENV_SECRET_KEY` when linking the default profile:

    ```sh
    env ENV_SECRET_KEY=test1234 ~/dotpy/dotpy link default
    ```

1. The rendered file will be linked into the home with the `.rendered` suffix removed and a dot prepended. In the example, this will result in the rendered file `default/env.rendered` being created and linked to `~/.env` with the below contents.

    ```sh
    export SECRET_KEY=test1234
    ```

1. Be sure to include `**/*.rendered` in `.gitignore` if you put your dotfiles into a git repository.

## Development

For linting, building and testing, see the [workflow](https://github.com/vincentqb/dotpy/blob/main/.github/workflows/python-app.yml).

![Test](https://github.com/vincentqb/dotpy/actions/workflows/python-app.yml/badge.svg)
