# Archive Workspace

This repository stores canonical Archive content in a separate repo.
It may be private or public.

## Requirements

This workspace repo depends on a separate Archive tool repo.

You need:

- `make`
- `podman`
- a local checkout of the Archive repo

## Layout

- `incoming/new/`: rough draft intake
- `incoming/review/`: normalized drafts waiting for approval
- `sources/notes/`: canonical notes
- `sources/docs/`: canonical docs

Generated `content/`, `site/`, and `.vitepress/*generated*` output stay in the Archive tool clone.
This bootstrap stays intentionally empty; the public repo's optional `examples/` starter content is not copied into the workspace repo.

## Usage

By default, the forwarding `Makefile` expects the Archive repo at `../archive`.
Set `ARCHIVE_DIR` in the forwarding `Makefile` or on the command line if your Archive clone lives elsewhere.
See `AGENTS.md` in this repo for workspace-local agent guidance.
That file includes generic guidance for agents that support specialist tools or subagents for exploration, verification, review, or research.
Treat it as a starting pont for your own environment and edit it freely if your preferred agent runtime uses different capabilities or conventions.

## If You Only Have This Workspace Repo

Clone the Archive repo separately:

```sh
git clone https://codeberg.org/rch/archive ../archive
```

Then confirm forwarding works from this workspace repo:

```sh
make help
```

If your Archive clone lives somewhere else:

```sh
make ARCHIVE_DIR=/path/to/archive help
```

## First Run

From this workspace repo:

```sh
make validate
make build
```

Use `make check` for a fuller verification pass.

Then run commands from this workspace repo:

```sh
make validate
make new kind=note title="DNS Notes" section=infra
make build
```

Those commands forward to Archive with `WORKSPACE=$(CURDIR)`.
Use this forwarding `Makefile` as the default interface when you are already inside the workspace repo.
The installed `archive` CLI is optional and is most useful for cross-project or external-agent workflows.

## Ownership

- this repo owns canonical `incoming/` and `sources/` content
- the Archive repo owns tooling, generated `content/`, generated `site/`, and generated `.vitepress/*` output
