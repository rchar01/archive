# Archive Workspace

This repository stores canonical Archive content in a separate repo.
It may be private or public.

## Requirements

This workspace repo depends on a separate Archive tool repo.

You need:

- `make`
- `podman`
- a local checkout of the Archive repo from `https://codeberg.org/rch/archive`

## Layout

- `incoming/new/`: rough draft intake
- `incoming/review/`: normalized drafts waiting for approval
- `sources/notes/`: canonical notes
- `sources/docs/`: canonical docs

Generated `content/`, `site/`, and `.vitepress/*generated*` output stay in the Archive tool clone.
This bootstrap stays intentionally empty; the public repo's optional `examples/` starter content is not copied into the workspace repo.

## If You Only Have This Workspace Repo

Clone the Archive repo separately and either place it at `../archive` or point this repo at it explicitly:

```sh
git clone https://codeberg.org/rch/archive ../archive
make help
```

If your Archive clone lives elsewhere:

```sh
make ARCHIVE_DIR=/path/to/archive help
```

## Usage

Set `ARCHIVE_DIR` in the forwarding `Makefile` if your Archive clone is not at `../archive`.
See `AGENTS.md` in this repo for workspace-local agent guidance.
That file includes generic guidance for agents that support specialist tools or subagents for exploration, verification, review, or research.
Treat it as a starting point for your own environment and edit it freely if your preferred agent runtime uses different capabilities or conventions.

Then run commands from this workspace repo:

```sh
make validate
make new kind=note title="DNS Notes" section=infra
make build
```

Those commands forward to Archive with `WORKSPACE=$(CURDIR)`.
Use this forwarding `Makefile` as the default interface when you are already inside the workspace repo.
The installed `archive` CLI is optional and is most useful for cross-project or external-agent workflows.

## First Run

From this workspace repo:

```sh
make validate
make build
```

Use `make check` for a fuller verification pass.

## Preview Server

Start the local VitePress preview server from this workspace repo:

```sh
make dev-bg
make dev-status
make dev-logs
```

Then open `http://localhost:5173`.

Stop it later with:

```sh
make dev-stop
```

Use `make dev` instead if you want the foreground dev server.

## Static Runtime Server

Build the static site and run the local Caddy runtime image:

```sh
make runtime-build
make runtime-run
make runtime-status
make runtime-logs
```

Then open `http://localhost:8080`.

Stop it later with:

```sh
make runtime-stop
```

`runtime-build` packages the prebuilt static site into the Caddy runtime image.

## Ownership

- this repo owns canonical `incoming/` and `sources/` content
- the Archive repo owns tooling, generated `content/`, generated `site/`, and generated `.vitepress/*` output
