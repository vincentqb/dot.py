# dotdash

dotdash is a minimalist script to manage links to dotfiles, inspired by [bashdot](https://github.com/bashdot/bashdot). It is a single script, written entirely in python, which is easily auditable, requiring no dependencies.

dotdash symlinks files and directories into the user's home directory from a directory known as a **profile**. It supports multiple profiles and file templates with variables. 

## Install

You can simply clone the repository.

```sh
git clone https://github.com/vincentqb/dotdash ~/dotdash
```

## Quick Start

1. Create your initial profile directory, in this example, **default**.

    ```sh
    mkdir default
    ```

1. Add any files you would like symlinked into your home directory when this profile is installed:

    ```sh
    echo 'set -o vi' > default/env
    ```

1. Install the profile.

    ```sh
    ~/dotdash/dotdash.py link default
    ```
    Note, when you run install, dotdash **prepends a dot**, in front of the original filename, to the linked file.

    In the above, **default/env** will now be linked to **~/.env**.

1. Continue adding your dotfiles to the default profile.

   ```sh
   mv ~/.bashrc default/bashrc
   ```

1. dotdash is indempotent so you can safely re-run the install command to link newly added files. Store this directory in a cloud drive or source control. Repeat for additional profiles.

## Templates

Values which need to be set in a file when dotdash is run can be placed in a template.

1. Append **.template** to any files which should be rendered.

1. When installed, template files will have all variables replaced with the current
environment variables set when dotdash is run.

1. The rendered files will be created in the same directory, and have **.template** replaced with **.rendered**.

1. The rendered file will be symlinked into the home directory with the .rendered suffix removed and a pre-prended dot.

1. For example:

    If you have the file **default/env.template** with the below contents:

    ```sh
    export SECRET_KEY=$ENV_SECRET_KEY
    ```

    You can run the following to set the value **ENV_SECRET_KEY** when installing the home profile:

    ```sh
    env ENV_SECRET_KEY=test1234 ~/dotdash/dotdash.py link default
    ```

    This will result in the rendered file **default/env.rendered** being created and symlinkd to **~/.env** with the below contents.

    ```sh
    export SECRET_KEY=test1234
    ```

1. Be sure to include **\*\*/\*.rendered** in **.gitignore** if you will be checking your dotfiles into a git repository.
