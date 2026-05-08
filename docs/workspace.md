# Workspace Mode

Workspace mode keeps canonical `incoming/` and `sources/` content in a separate repository while the Archive clone remains the toolchain and generated-output location.

The workspace repo may be private or public.

## Bootstrap

Create the workspace repo skeleton with the Archive tool clone:

```sh
git clone https://codeberg.org/rch/archive ~/tools/archive
mkdir -p ~/repos/my-notes

make -C ~/tools/archive WORKSPACE=~/repos/my-notes init-workspace
```

Do not copy files out of `scripts/tasks/templates/workspace/` manually. Those files are internal templates used by `make init-workspace`.

That creates:

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

It does not copy the public repo's starter examples. A new workspace repo begins with empty `sources/notes/` and `sources/docs/` trees.

You can rerun `make -C ~/tools/archive WORKSPACE=~/repos/my-notes init-workspace` on an existing workspace repo.
By default it only creates missing directories and missing root bootstrap files, so existing `sources/...` content and existing root files are preserved.
Use `make -C ~/tools/archive WORKSPACE=~/repos/my-notes FORCE=1 init-workspace` when you intentionally want to refresh the root `.gitignore`, `README.md`, `AGENTS.md`, and forwarding `Makefile` templates.
`archive init-workspace --force ~/repos/my-notes` remains available too.
The generated `AGENTS.md` is a default workspace-local guide for LLMs and agents; customize it for your own runtime if needed.

## Forwarding Makefile

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

- `make`
- `podman`
- a local checkout of the Archive repo from `https://codeberg.org/rch/archive`

If you cloned only the workspace repo, clone the Archive repo separately and confirm forwarding works:

```sh
git clone https://codeberg.org/rch/archive ../archive
make help
```

Or point at a different Archive checkout explicitly:

```sh
make ARCHIVE_DIR=/path/to/archive help
```

## Daily Usage

From inside the workspace repo:

```sh
make validate
make new kind=note title="DNS Notes" section=infra
make process-incoming
make build
```

Inside the workspace repo, `make` is the default human-facing interface.
The installed `archive` CLI is most useful when you are operating from other repositories or when external agents need to target this workspace explicitly.

## Multiple Workspaces, One Archive Clone

One Archive clone can host multiple workspace repos at the same time.

- canonical `incoming/` and `sources/` content still live in each workspace repo
- generated output stays in the Archive tool repo under `.instances/<instance>/...`
- the workspace template defaults `ARCHIVE_INSTANCE` to the workspace directory name

If you want multiple live preview servers, use different ports:

```sh
make ARCHIVE_INSTANCE=notes-a VITEPRESS_DEV_PORT=5173 dev-bg
make ARCHIVE_INSTANCE=notes-b VITEPRESS_DEV_PORT=5174 dev-bg
```

If you want multiple local runtime containers, use different ports there too:

```sh
make ARCHIVE_INSTANCE=notes-a RUNTIME_PORT=8080 runtime-run
make ARCHIVE_INSTANCE=notes-b RUNTIME_PORT=8081 runtime-run
```

## Preview Server

Start the local VitePress preview server from the workspace repo:

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

Canonical content stays in the workspace repo. Generated output stays in the Archive tool repo, either in the standalone root paths or under `.instances/<instance>/...` for workspace-instance runs.

For the recommended pinned CI and Kubernetes-oriented packaging flow, see `docs/workspace-ci.md`.
