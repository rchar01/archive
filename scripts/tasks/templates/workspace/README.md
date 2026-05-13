# Archive Workspace

This repository stores canonical Archive content in a separate repo.
It may be private or public.

## Requirements

This workspace repo depends on a separate Archive tool repo.

You need:

- `podman`
- a local checkout of the Archive repo from `https://codeberg.org/rch/archive`
- the installed `archive` launcher from that checkout, unless you use the optional forwarding `Makefile`

## Layout

- `incoming/new/`: rough draft intake
- `incoming/review/`: normalized drafts waiting for approval
- `sources/notes/`: canonical notes
- `sources/docs/`: canonical docs

Generated output stays in the Archive tool clone. In workspace-instance mode, it lands under `.instances/<instance>/...` there.
This bootstrap stays intentionally empty; the public repo's optional `examples/` starter content is not copied into the workspace repo.

## If You Only Have This Workspace Repo

Clone the Archive repo separately and install the launcher:

```sh
git clone https://codeberg.org/rch/archive ../archive
../archive/scripts/install-cli
archive --help
```

If you prefer the optional forwarding `Makefile` and your Archive clone lives elsewhere:

```sh
make ARCHIVE_DIR=/path/to/archive help
```

## Usage

The installed `archive` command is the preferred workspace interface and discovers this workspace from the current directory.
The optional forwarding `Makefile` defaults `ARCHIVE_INSTANCE` to the workspace directory name so one Archive clone can host multiple workspaces concurrently.
See `AGENTS.md` in this repo for workspace-local agent guidance.
That file includes generic guidance for agents that support specialist tools or subagents for exploration, verification, review, or research.
Treat it as a starting point for your own environment and edit it freely if your preferred agent runtime uses different capabilities or conventions.

Then run commands from this workspace repo:

```sh
archive validate
archive new note --title "DNS Notes" --section infra
archive build
```

Use the forwarding `Makefile` if your local workflow already standardizes on `make`; it forwards to Archive with `WORKSPACE=$(CURDIR)`.

## First Run

From this workspace repo:

```sh
archive validate
archive build
```

Use `archive check` for a fuller verification pass.

## Preview Server

Start the local VitePress preview server from this workspace repo:

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

To run multiple workspace preview servers from one Archive clone, use different ports and, if needed, different explicit instance names:

```sh
ARCHIVE_INSTANCE=notes-a VITEPRESS_DEV_PORT=5173 archive dev-bg
ARCHIVE_INSTANCE=notes-b VITEPRESS_DEV_PORT=5174 archive dev-bg
```

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

To run multiple local runtime servers from one Archive clone, use different ports and, if needed, different explicit instance names:

```sh
ARCHIVE_INSTANCE=notes-a RUNTIME_PORT=8080 archive runtime-run
ARCHIVE_INSTANCE=notes-b RUNTIME_PORT=8081 archive runtime-run
```

## Ownership

- this repo owns canonical `incoming/` and `sources/` content
- the Archive repo owns tooling and generated output, including instance-scoped output under `.instances/<instance>/...`
