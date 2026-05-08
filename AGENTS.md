# Agents

## Read First

- Read `README.md`, `docs/README.md`, `Makefile`, `package.json`, `Containerfile.dev`, `Containerfile.runtime`, `requirements.txt`, and the scripts under `scripts/` before structural changes.
- Prefer executable sources of truth over prose. If docs conflict with scripts or config, trust the scripts/config and update docs.
- There is no checked-in CI workflow in this repo; the real verification surface is `Makefile`, the executable scripts under `scripts/`, and the tests under `tests/`.

## Platform Shape

- Target flow: `incoming/ -> sources/ -> content/ -> site/`
- Workflow discovery is dynamic; the repo currently ships `note` and `doc`
- `sources/` is canonical editable content
- `content/` and `site/` are generated
- `.vitepress/nav.generated.ts`, `.vitepress/sidebar.generated.ts`, and `.vitepress/knowledge/*.generated.json` are generated
- Archive supports two modes: standalone and workspace mode
- in workspace mode, canonical `incoming/` and `sources/` live under `WORKSPACE` while generated `content/`, `site/`, `build/`, and generated `.vitepress/*` output stay in the Archive tool repo
- canonical frontmatter may use `slug` for stable generated routes and `nav_title` for compact navigation labels
- canonical source pages may keep page-local assets in sibling `<page-stem>.assets/` directories and reference them with ordinary relative Markdown paths
- canonical workflow-local section display overrides may live in sibling `_sections.yaml` files under `sources/<workflow>/`; use those for labels like `OMV` or default sidebar collapse behavior instead of encoding display casing into `section`
- canonical source pages may use plain ` ```mermaid ` fences; the local VitePress theme renders them client-side, so do not replace them with manual Vue components in page content
- `incoming/new/` and `incoming/review/` are the only intake queues
- `Containerfile.runtime` packages a prebuilt static site into a self-contained Caddy image

## Architecture

- `scripts/core/`: reusable platform primitives only
- `scripts/workflows/`: workflow-local behavior only
- `scripts/tasks/`: thin executable orchestration only
- `scripts/runtime/`: container and runtime helpers only

## Workflow Discovery

- Workflow configuration is workflow-local.
- `scripts/core/registry.py` should discover workflows by scanning `scripts/workflows/*/workflow.yml`.
- Do not add a central `registry/workflows.yml`.
- A workflow should be mostly self-contained inside one folder.
- Navigation, workflow overview pages, and sidebar content should follow non-empty discovered workflows.

## Boundaries

- Do not put workflow-specific behavior in `scripts/core/`.
- Do not put orchestration logic in workflow modules.
- Do not put business logic in runtime scripts.

Good examples:

- `scripts/core/frontmatter.py` parses frontmatter
- `scripts/workflows/note/validator.py` checks note-specific sections
- `scripts/tasks/process_incoming.py` decides whether to write to `sources/` or `incoming/review/`
- `scripts/runtime/dev` rebuilds content and starts the dev server

## Refactor Rules

- Do not recreate the removed archive workflow.
- Use `docs/` for human-facing documentation only. Do not use it as a canonical content root or recreate the old archive compatibility structure under `processed/`, `org/`, `scripts/adapters/`, `scripts/renderers/`, or `scripts/pipelines/`.
- Keep new work inside the current architecture: `incoming/`, `sources/`, `content/`, `site/`, `scripts/core/`, `scripts/workflows/`, `scripts/tasks/`, and `scripts/runtime/`.
- If a target directory does not exist yet, create it in that current architecture instead of reviving the old structure.
- Prefer direct execution through `scripts/tasks/*.py` and `scripts/runtime/*`.

## Commands

- `make container-build` builds the dev image from `Containerfile.dev`.
- `make install-cli` installs the user-facing `archive` command into `~/.local/bin` by default.
- `make install-skill` installs the project-shipped `archive-authoring` skill into `~/.agents/skills` by default.
- `make uninstall-skill` removes the project-shipped `archive-authoring` skill from `~/.agents/skills` by default.
- `make devshell` opens an interactive shell inside the dev container.
- `make new` creates a canonical source file.
- `make init-workspace` bootstraps a workspace repo skeleton at `WORKSPACE`.
- `make process-incoming` normalizes files from `incoming/new/`.
- `make accept-review` moves a reviewed draft into `sources/`.
- `make validate` validates canonical sources.
- `make build-content` rebuilds generated content, copies sibling `.assets/` directories beside generated pages, rebuilds knowledge metadata, home/index pages, and sidebar/nav data.
- `make dev` rebuilds content and starts VitePress dev mode in the container.
- `make dev-bg` starts the VitePress dev server in the background.
- `make dev-logs`, `make dev-status`, and `make dev-stop` manage the background dev server container.
- `make build` rebuilds content and builds the static site.
- `make runtime-build` packages the prebuilt `site/` output into the Caddy runtime image.
- `make runtime-run`, `make runtime-logs`, `make runtime-status`, and `make runtime-stop` manage the local runtime container.
- `make check` runs validation, rebuilds content, and runs the VitePress build.
- `make doctor` checks repository health.

## Agent Workflow Expectations

- Read relevant code before editing.
- Prefer minimal changes that match existing patterns.
- Keep workflow-specific behavior out of `scripts/core/` unless it is truly shared platform behavior.
- Keep `README.md`, `AGENTS.md`, and skill docs current when repository behavior changes.
- When docs mention canonical content paths, distinguish `WORKSPACE`-owned paths from Archive tool-repo generated paths.
- Keep local page assets in sibling `<page-stem>.assets/` directories under `sources/`; do not hand-edit copied asset folders under `content/`.
- Keep canonical `section` paths lowercase and slash-separated; use `sources/<workflow>/_sections.yaml` for display-label overrides.
- Preserve explicit `slug` and `nav_title` unless the task is specifically about changing routes or navigation labels.
- Use a verification-focused subagent for non-trivial test runs or runtime-backed checks.
- Use a review-focused subagent after substantial edits to catch regressions and doc/code drift.
- Use a research-focused subagent when behavior depends on external tooling or upstream docs.
- Summarize any subagent findings you rely on.
- Do not revert unrelated worktree changes.

Final rule:

```text
core = reusable platform primitives
workflows = workflow-specific behavior
tasks = executable orchestration
runtime = container/dev/server helpers
```
