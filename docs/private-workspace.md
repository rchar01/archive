# Private Workspace

Private workspace mode keeps canonical `incoming/` and `sources/` content in a separate private Git repository while the public Archive clone remains the toolchain and generated-output location.

## Bootstrap

Create the private repo skeleton with the Archive tool clone:

```sh
git clone <archive> ~/tools/archive
mkdir -p ~/private/my-notes

make -C ~/tools/archive WORKSPACE=~/private/my-notes init-workspace
```

Do not copy files out of `scripts/tasks/templates/private-workspace/` manually. Those files are internal templates used by `make init-workspace`.

That creates:

```text
incoming/new/
incoming/review/
sources/notes/
sources/docs/
.gitignore
README.md
Makefile
```

It does not copy the public repo's starter examples. A new private workspace begins with empty `sources/notes/` and `sources/docs/` trees.

## Forwarding Makefile

The generated private-repo `Makefile` forwards commands to Archive with `WORKSPACE=$(CURDIR)`.

By default it expects the public Archive clone at `../archive`:

```make
ARCHIVE_DIR ?= ../archive
WORKSPACE := $(CURDIR)
```

Update `ARCHIVE_DIR` if your public Archive clone lives elsewhere.

## Daily Usage

From inside the private repo:

```sh
make validate
make new kind=note title="DNS Notes" section=infra
make process-incoming
make build
```

Inside the private repo, `make` is the default human-facing interface.
The installed `archive` CLI is most useful when you are operating from other repositories or when external agents need to target this workspace explicitly.

Canonical content stays in the private repo. Generated `content/`, `site/`, and generated `.vitepress/*` artifacts stay in the public Archive tool repo.

For the recommended pinned CI and Kubernetes-oriented packaging flow, see `docs/private-ci.md`.
