# Archive

<div align="center">
  <img src=".vitepress/public/brand/archive-forge-avatar-transparent-512.png" alt="Archive forge avatar" width="256">
</div>

Archive is a source-first documentation pipeline built around VitePress and Python workflow automation.

Archive supports two usage modes:

- standalone mode: clone `archive` and keep canonical content in that repo
- workspace mode: use the `archive` clone as tooling and keep canonical `incoming/` and `sources/` content in a separate repo

## What Archive Adds

Compared with plain VitePress, Archive adds:

- a canonical publishing pipeline: `incoming/ -> sources/ -> content/ -> site/`
- workflow-aware authoring for `note` and `doc`, with dynamic workflow discovery for future additions
- generated home, workflow, and tag index pages plus generated top-nav and sidebar data
- a knowledge panel with generated related links, backlinks, metadata, tag navigation, and local tag-search support such as exact `#tag`, prefix `#tag*`, and tag-qualified text queries like `#tag text`
- an optional `/graph/` knowledge map for browsing generated links, related entries, and tag relationships
- an intake and review flow for rough imported Markdown before it becomes canonical content
- workspace mode, where canonical content lives in a separate repo while generated output stays in the Archive tool repo
- instance-scoped generated output via `ARCHIVE_INSTANCE` so one Archive clone can serve multiple workspaces concurrently
- source-adjacent asset copying and built-in Mermaid fence rendering in the local theme

## Quickstart

Archive supports two first-run paths. Start with standalone mode unless your canonical content should live in a separate repo.

### Standalone Mode

Use this when you want the simplest out-of-the-box workflow.

```sh
git clone https://codeberg.org/rch/archive
cd archive
make install
make check
make dev-bg
```

Then open `http://localhost:5173`.

The public repo ships a tiny starter corpus under `sources/notes/examples/` and `sources/docs/examples/` so the first build shows real content, local assets, Mermaid rendering, and knowledge-panel links.
Delete those two `examples/` directories and run `make build` if you want to start from a blank standalone corpus.

### Workspace Mode

Use this when canonical docs and notes should stay in a separate repo while Archive remains the tooling repo.

```sh
git clone https://codeberg.org/rch/archive ~/tools/archive
~/tools/archive/scripts/install-cli
mkdir -p ~/repos/my-notes

archive init-workspace ~/repos/my-notes
archive check --workspace ~/repos/my-notes
archive dev-bg --workspace ~/repos/my-notes
```

Then open `http://localhost:5173`.

Workspace bootstrap stays empty on purpose; it does not copy the public starter examples into your workspace repo.
You can safely rerun `archive init-workspace ~/repos/my-notes`; by default it only fills in missing directories and missing root bootstrap files.
Use `archive init-workspace --force ~/repos/my-notes` when you intentionally want to refresh the root `.gitignore`, `README.md`, `AGENTS.md`, and forwarding `Makefile` templates.
Use `archive init-workspace --no-makefile ~/repos/my-notes` when you want a CLI-only workspace.

### Shared Prerequisites

- `podman`
- `make` for standalone/repo-contributor workflows; workspace users can use the installed `archive` CLI without a workspace Makefile

### Shared Commands

Initial setup and verification from the Archive tool repo:

```sh
make install
make check
```

Install the CLI for workspace and cross-project use:

```sh
make install-cli
archive --help
```

Optional installable global skill for agents in other repos:

```sh
make install-skill
```

Start the local preview server from the active mode:

```sh
make dev-bg
make dev-status
make dev-logs
```

Stop the preview server:

```sh
make dev-stop
```

Package the runtime image after building the static site:

```sh
make build
make runtime-build
make runtime-run
```

`runtime-build` packages the prebuilt `site/` output; it does not rebuild canonical content inside the runtime image build.

Create your first canonical page directly:

```sh
archive new note --title "Hello Archive" --section getting-started
archive validate
archive build
```

Or start from a rough draft placed in `incoming/new/`:

```sh
archive process
archive build
```

For the full authoring flow, including when to use `archive new` versus intake/review, read `docs/authoring.md`.

All content-oriented `make` targets accept `WORKSPACE`, which defaults to `.`. The installed `archive` CLI also accepts `--workspace` and can infer it from inside a workspace repo:

```sh
archive validate --workspace .
```

The public command form is `archive <command> --workspace <canonical-root>` or `make WORKSPACE=<canonical-root> <target>`.
`WORKSPACE` selects the canonical content root for `incoming/` and `sources/` while generated output stays in the Archive tool repo.
`ARCHIVE_INSTANCE` selects the generated-output namespace inside the Archive tool repo. Standalone mode defaults to `default`; workspace repos default to their directory name.
`ARCHIVE_KNOWLEDGE_GRAPH=0` disables the generated `/graph/` page, top-nav item, and home Browse card for builds that do not want the graph surface.

For the supported workspace repo layout, see `docs/workspace.md`.
For a workspace repo CI and Kubernetes-oriented packaging flow, see `docs/workspace-ci.md`.

## Ownership Model

### Workspace Repo Owns

- `incoming/`
- `incoming/new/`
- `incoming/review/`
- `sources/`
- `sources/notes/`
- `sources/docs/`
- the optional forwarding workspace-repo `Makefile`
- the workspace-repo `README.md`
- the workspace-repo `.gitignore`

### Archive Tool Repo Owns

- `scripts/`
- `Makefile`
- `.vitepress/`, including static site assets under `.vitepress/public/`
- standalone generated `content/`, `site/`, and `build/`
- instance-scoped generated output under `.instances/<instance>/...` in workspace mode or when `ARCHIVE_INSTANCE` is set explicitly
- generated nav/sidebar data and generated knowledge metadata
- `Containerfile.dev`
- `Containerfile.runtime`
- `Caddyfile.runtime`

In workspace mode, canonical content stays in the workspace repo while generated output stays in the Archive tool repo.

## Architecture

Archive is built around one rule: edit canonical content in `sources/`, then generate everything else.

```text
incoming/ -> sources/ -> content/ -> site/
```

Rules:

- `incoming/` is temporary intake
- `sources/` is canonical editable content
- `content/` is generated VitePress input
- `site/` is generated static output
- workflows are discovered from `scripts/workflows/*/workflow.yml`
- the repo currently ships `note` and `doc`, and users may add more workflows later
- `Containerfile.runtime` packages a prebuilt static site into a self-contained Caddy image

## Repository Layout

- `incoming/new/`: rough Markdown captures
- `incoming/review/`: normalized drafts waiting for approval
- `sources/notes/`: canonical note sources
- `sources/docs/`: canonical doc sources
- `content/`: standalone generated VitePress source tree
- `site/`: standalone generated static site output
- `.instances/`: instance-scoped generated content, site, build, and generated data for concurrent workspace runs
- `docs/`: human-facing documentation and reference guides
- `.vitepress/`: repo-root VitePress config, local theme, tool-owned public assets, and standalone generated metadata
- `.vitepress/public/brand/`: site logo, favicon, and reusable forge avatar assets
- `scripts/core/`: reusable platform primitives
- `scripts/workflows/`: workflow-local note/doc behavior
- `scripts/tasks/`: thin executable orchestration
- `scripts/runtime/`: container and runtime helpers

Workflow config is discovered from `scripts/workflows/*/workflow.yml`.

In workspace mode, treat the layout above as the Archive tool repo layout. The workspace repo layout is documented in `docs/workspace.md`.

## Documentation

Human-facing documentation lives under `docs/`.

Start with:

- `docs/README.md`: documentation index
- `docs/cli.md`: installed workspace and cross-project command wrapper
- `docs/skills.md`: installable global skill for cross-project agents
- `docs/authoring.md`: end-to-end human and agent authoring playbook
- `docs/note.md`: note-specific structure and rules
- `docs/doc.md`: doc-specific structure and rules
- `docs/workspace.md`: workspace repo bootstrap flow, installed CLI use, and optional forwarding `Makefile`
- `docs/workspace-ci.md`: workspace CI checkout, build, packaging, and deployment pattern
- `THIRD_PARTY_NOTICES.md`: attribution and license notices for bundled third-party assets

## Authoring Features

Archive adds workflow-aware authoring and generated UI around VitePress:

- source frontmatter supports stable `slug`, compact `nav_title`, summaries, tags, curated related links, and knowledge-panel hide flags
- workflow-local `_sections.yaml` files can override sidebar/index section labels and default collapse state
- source-adjacent `<page-stem>.assets/` directories are copied beside generated pages
- plain ` ```mermaid ` fences render through the local VitePress theme
- generated indexes, sidebar/nav data, tag pages, backlinks, related suggestions, and knowledge metadata are machine-owned output
- local search supports normal full-text queries plus exact, prefix, and tag-qualified hashtag queries such as `#proxmox`, `#proxmo*`, and `#proxmox network`

For the source format, metadata fields, linking rules, local assets, Mermaid, search, and validation loops, use `docs/authoring.md` as the source of truth.

## Commands

Use `archive --help` for the installed CLI command surface.
Use `make help` from the Archive tool repo for contributor and compatibility targets.

## Development Verification

Run the Python test suite and full Archive check before release-oriented changes:

```sh
python3 -m unittest discover tests
make check
```

`make check` validates sources, rebuilds generated content and metadata, and runs the VitePress static build.
