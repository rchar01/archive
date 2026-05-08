# Installed CLI

Use the installed `archive` command when you want to operate on Archive content from other directories or other projects.

## Install

Install the launcher into `~/.local/bin`:

```sh
make install-cli
```

Override the target bin directory if needed:

```sh
BIN_DIR=/custom/bin make install-cli
```

The installed launcher points at this checked-out Archive repository.
If you move the Archive clone later, reinstall the CLI.

If you also want cross-project agents to understand the Archive workflow without repo-local context, install the project-shipped skill documented in `docs/skills.md`.

## Workspace Resolution

The CLI infers `--workspace` when you run it from inside a valid Archive workspace.

That includes:

- the standalone Archive repo
- a workspace repo created with `archive init-workspace` or `make init-workspace`

When you run the command elsewhere, pass `--workspace /path/to/repo` explicitly.

## Bootstrap Behavior

`archive init-workspace PATH` is safe to rerun on an existing workspace repo.

- by default it creates any missing `incoming/...` and `sources/...` directories and only writes missing root bootstrap files
- it does not delete or overwrite existing canonical content under `sources/...`
- pass `--force` only when you intentionally want to overwrite the root `.gitignore`, `README.md`, and forwarding `Makefile` templates

## Common Commands

Create a canonical note or doc:

```sh
archive new note --title "DNS Notes" --section infra
archive new doc --title "Homelab Firewall" --section homelab/networking
```

Import a raw Markdown file from another location into the intake queue:

```sh
archive import ~/Downloads/raw.md \
  --workspace ~/repos/my-notes \
  --kind doc \
  --section inbox \
  --processing review
```

Normalize the intake queue and accept a reviewed draft:

```sh
archive process --workspace ~/repos/my-notes
archive accept incoming/review/raw.md --workspace ~/repos/my-notes
```

Validate and build:

```sh
archive validate --workspace ~/repos/my-notes
archive build --workspace ~/repos/my-notes
archive check --workspace ~/repos/my-notes
```

## Command Surface

- `archive init-workspace PATH [--force]`
- `archive new note ...`
- `archive new doc ...`
- `archive import FILE ...`
- `archive process`
- `archive accept FILE`
- `archive validate`
- `archive build-content`
- `archive build`
- `archive check`
