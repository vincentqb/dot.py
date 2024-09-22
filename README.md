# dot.py

**dot.py** is a minimalist one-file python script for managing dotfiles via symbolic links. Inspired by [bashdot](https://github.com/bashdot/bashdot), it supports multiple profiles and customizable file templates with variables. No external dependencies, just **python 3.6+**.

## Quick Start

1. Install and run with `dot.py` below

   ```sh
   pip install dot.py
   ```

   or download the script directly and run with `~/dot.py` below

   ```sh
   wget https://raw.githubusercontent.com/vincentqb/dot.py/main/dot.py -O ~/dot.py && chmod u+x ~/dot.py
   ```

1. Create your initial profile. For example, you can create a directory called `default`.

   ```sh
   mkdir default
   ```

1. Add any files you would like linked into your home when this profile is linked.

   ```sh
   mv ~/.bashrc default/bashrc
   ```

1. Link the profile. When you link, dot.py prepends a dot, in front of the original file name, to the linked file. Below, `default/bashrc` will be linked to `~/.bashrc`.

   ```sh
   dot.py link default
   ```

1. You can safely re-run to link newly added files. Store this profile in a cloud drive or source control. Repeat for additional profiles.

## Templates

Values which need to be set in a file when dot.py is run can be placed in a template.

1. Append `.template` to any files which should be rendered. For example, assume you have a file `default/bashrc.template` containing:

   ```sh
   export SECRET_KEY=$ENV_SECRET_KEY
   ```

1. The rendered files will be created in the same directory, and have `.template` replaced with `.rendered`. In the example, you can run the following to set the value `ENV_SECRET_KEY` when linking the default profile.

   ```sh
   env ENV_SECRET_KEY=test1234 dot.py link default
   ```

1. The rendered file will be linked into the home with the `.rendered` suffix removed and a dot prepended. In the example, this will result in the rendered file `default/bashrc.rendered` being created and linked to `~/.bashrc` with the below contents.

   ```sh
   export SECRET_KEY=test1234
   ```

1. Be sure to include `**/*.rendered` in `.gitignore` [like so](https://github.com/vincentqb/dot.py/blob/main/.gitignore#L1) if you put your dotfiles into a git repository.

## Development

For linting, building and testing, see the [workflow](https://github.com/vincentqb/dot.py/blob/main/.github/workflows/python-app.yml).

![Test](https://github.com/vincentqb/dot.py/actions/workflows/python-app.yml/badge.svg)
