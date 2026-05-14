# Installed CLI

Use the installed `archive` command when you want to operate on Archive content from a workspace repo or from other directories and projects.

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
The launcher is a Bash dispatcher around the Archive tool repo; it keeps Makefile as a contributor convenience instead of requiring a Makefile in every workspace repo.

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
- pass `--force` only when you intentionally want to overwrite the root `.gitignore`, `README.md`, `AGENTS.md`, and forwarding `Makefile` templates
- pass `--no-makefile` when you want a CLI-only workspace without a forwarding `Makefile`

The equivalent Make workflow is `make WORKSPACE=/path/to/workspace FORCE=1 init-workspace`.
Use `NO_MAKEFILE=1` with that Make target when you want the CLI-only workspace form.

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

Disable the generated knowledge graph for a build:

```sh
ARCHIVE_KNOWLEDGE_GRAPH=0 archive build --workspace ~/repos/my-notes
```

`ARCHIVE_KNOWLEDGE_GRAPH` defaults to enabled. Set it to `0`, `false`, `no`, or `off` to omit the `/graph/` page, top-nav item, and home Browse card while keeping generated knowledge-panel metadata available.

From inside a workspace repo, the `--workspace` option is optional:

```sh
archive validate
archive build
archive dev-bg
```

## Command Surface

- `archive init-workspace PATH [--force] [--no-makefile]`
- `archive new note ...`
- `archive new doc ...`
- `archive import FILE ...`
- `archive process`
- `archive accept FILE`
- `archive validate`
- `archive build-content`
- `archive build-linkgraph`
- `archive build-related`
- `archive indexes`
- `archive sidebar`
- `archive build`
- `archive check`
- `archive dev`
- `archive dev-bg`
- `archive dev-status`
- `archive dev-logs`
- `archive dev-stop`
- `archive runtime-build`
- `archive runtime-run`
- `archive runtime-status`
- `archive runtime-logs`
- `archive runtime-stop`
