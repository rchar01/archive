# Installable Skills

This directory contains Archive skills that ship with the repository but are **not** auto-loaded from the project.

Use these when you want to install Archive guidance into your global agent skill directory manually.

Current skill:

- `archive-authoring/`: cross-project Archive authoring via the installed `archive` CLI

Install the skill globally from the Archive repo:

```sh
make install-skill
```

Uninstall it later:

```sh
make uninstall-skill
```

By default the installer targets `~/.agents/skills`.
Override that location with `SKILLS_DIR=/path/to/skills`.
