# Workspace Mode

Workspace mode keeps canonical `incoming/` and `sources/` content in a separate repository while the Archive clone remains the toolchain and generated-output location.

The workspace repo may be private or public.

## Bootstrap

Create the workspace repo skeleton with the Archive tool clone and installed CLI:

```sh
git clone https://codeberg.org/rch/archive ~/tools/archive
~/tools/archive/scripts/install-cli
mkdir -p ~/repos/my-notes

archive init-workspace ~/repos/my-notes
```

Do not copy files out of `scripts/tasks/templates/workspace/` manually. Those files are internal templates used by `archive init-workspace` and `make init-workspace`.

By default, that creates:

```text
incoming/new/
incoming/review/
sources/notes/
sources/docs/
.gitignore
README.md
AGENTS.md
Makefile
```

The forwarding `Makefile` is optional. Use `archive init-workspace --no-makefile ~/repos/my-notes` when you want a CLI-only workspace; this skips writing the Makefile but does not delete an existing one.

It does not copy the public repo's starter examples. A new workspace repo begins with empty `sources/notes/` and `sources/docs/` trees.

You can rerun `archive init-workspace ~/repos/my-notes` on an existing workspace repo.
By default it only creates missing directories and missing root bootstrap files, so existing `sources/...` content and existing root files are preserved.
Use `archive init-workspace --force ~/repos/my-notes` when you intentionally want to refresh the root `.gitignore`, `README.md`, `AGENTS.md`, and forwarding `Makefile` templates.
The equivalent Make workflow is `make -C ~/tools/archive WORKSPACE=~/repos/my-notes FORCE=1 init-workspace`.
The generated `AGENTS.md` is a default workspace-local guide for LLMs and agents; customize it for your own runtime if needed.

## Installed CLI and Forwarding Makefile

The installed `archive` command is the preferred workspace interface. It discovers the workspace from the current directory, so these commands work from inside a workspace repo:

```sh
archive validate
archive new note --title "DNS Notes" --section infra
archive process
archive build
```

The generated workspace-repo `Makefile` remains available for users who prefer `make`.

The generated workspace-repo `Makefile` forwards commands to Archive with `WORKSPACE=$(CURDIR)`.

By default it expects the Archive clone at `../archive`:

```make
ARCHIVE_DIR ?= ../archive
WORKSPACE := $(CURDIR)
ARCHIVE_INSTANCE ?= $(notdir $(CURDIR))
```

Update `ARCHIVE_DIR` if your Archive clone lives elsewhere.
`ARCHIVE_INSTANCE` selects the generated-output namespace inside the Archive tool repo; override it if you need a different stable name.

## Requirements

Workspace mode depends on a separate Archive tool repo checkout.

You need:

- `podman`
- a local checkout of the Archive repo from `https://codeberg.org/rch/archive`
- the installed `archive` launcher from that checkout, unless you use the optional forwarding `Makefile`

If you cloned only the workspace repo, clone the Archive repo separately and install the launcher:

```sh
git clone https://codeberg.org/rch/archive ../archive
../archive/scripts/install-cli
archive --help
```

Or use the optional forwarding Makefile and point at a different Archive checkout explicitly:

```sh
make ARCHIVE_DIR=/path/to/archive help
```

## Daily Usage

From inside the workspace repo:

```sh
archive validate
archive new note --title "DNS Notes" --section infra
archive process
archive build
```

Inside the workspace repo, `archive` is the default human-facing interface. The forwarding `Makefile` is still useful when a local workflow or CI job already standardizes on `make`.

## Multiple Workspaces, One Archive Clone

One Archive clone can host multiple workspace repos at the same time.

- canonical `incoming/` and `sources/` content still live in each workspace repo
- generated output stays in the Archive tool repo under `.instances/<instance>/...`
- the installed CLI and workspace template default `ARCHIVE_INSTANCE` to the workspace directory name

If you want multiple live preview servers, use different ports:

```sh
ARCHIVE_INSTANCE=notes-a VITEPRESS_DEV_PORT=5173 archive dev-bg
ARCHIVE_INSTANCE=notes-b VITEPRESS_DEV_PORT=5174 archive dev-bg
```

If you want multiple local runtime containers, use different ports there too:

```sh
ARCHIVE_INSTANCE=notes-a RUNTIME_PORT=8080 archive runtime-run
ARCHIVE_INSTANCE=notes-b RUNTIME_PORT=8081 archive runtime-run
```

## Preview Server

Start the local VitePress preview server from the workspace repo:

```sh
archive dev-bg
archive dev-status
archive dev-logs
```

Then open `http://localhost:5173`.

Stop it later with:

```sh
archive dev-stop
```

Use `archive dev` instead if you want the foreground dev server.

## Static Runtime Server

Build the static site and run the local Caddy runtime image:

```sh
archive runtime-build
archive runtime-run
archive runtime-status
archive runtime-logs
```

Then open `http://localhost:8080`.

Stop it later with:

```sh
archive runtime-stop
```

`runtime-build` packages the prebuilt static site into the Caddy runtime image.

Canonical content stays in the workspace repo. Generated output stays in the Archive tool repo, either in the standalone root paths or under `.instances/<instance>/...` for workspace-instance runs.

For the recommended pinned CI and Kubernetes-oriented packaging flow, see `docs/workspace-ci.md`.
