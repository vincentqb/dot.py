# dot.py

**dot.py** is a minimalist python script for managing dotfiles via symbolic links. Inspired by [bashdot](https://github.com/bashdot/bashdot), it supports multiple profiles and customizable file templates with variables. No external dependencies, just **python 3.6+**.

## Install and Help

You can simply clone the repository and call with `~/dot.py/dot.py -h`:

```sh
git clone https://github.com/vincentqb/dot.py ~/dot.py
```

Alternatively, you can install with pip and call with `dot.py -h`:

```sh
pip install dot.py
```

## Quick Start

1. Create your initial profile. For example, we create a directory called `default`.

    ```sh
    mkdir default
    ```

1. Add any files you would like linked into your home when this profile is linked.

    ```sh
    echo 'set -o vi' > default/env
    ```

1. Link the profile. When you link, dot.py prepends a dot, in front of the original file name, to the linked file. Below, `default/env` will be linked to `~/.env`.

    ```sh
    ~/dot.py/dot.py link default
    ```

1. Continue adding your dotfiles to the default profile.

   ```sh
   mv ~/.bashrc default/bashrc
   ```

1. You can safely re-run the link command to link newly added files. Store this profile in a cloud drive or source control. Repeat for additional profiles.

## Templates

Values which need to be set in a file when dot.py is run can be placed in a template.

1. Append `.template` to any files which should be rendered. For example, assume you have a file `default/env.template` containing:

    ```sh
    export SECRET_KEY=$ENV_SECRET_KEY
    ```

1. The rendered files will be created in the same directory, and have `.template` replaced with `.rendered`. In the example, you can run the following to set the value `ENV_SECRET_KEY` when linking the default profile:

    ```sh
    env ENV_SECRET_KEY=test1234 ~/dot.py/dot.py link default
    ```

1. The rendered file will be linked into the home with the `.rendered` suffix removed and a dot prepended. In the example, this will result in the rendered file `default/env.rendered` being created and linked to `~/.env` with the below contents.

    ```sh
    export SECRET_KEY=test1234
    ```

1. Be sure to include `**/*.rendered` in `.gitignore` if you put your dotfiles into a git repository.

## Testing

Run tests with `python3 -m pytest` from the root of the repository.

![Test and Build](https://github.com/vincentqb/dot.py/actions/workflows/python-app.yml/badge.svg)
