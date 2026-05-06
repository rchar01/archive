---
name: archive-manager
description: Manage this archive repository workflow for source intake, workflow edits, generated output rebuilds, and local dev/runtime operations.
compatibility: opencode
metadata:
  audience: maintainers
  workflow: archive
  domain: publishing
---

# Archive Manager

## Purpose

Use this skill for operational work in this repository.

Load it when the user wants to:

* add or edit canonical content in `sources/`
* process rough Markdown from `incoming/new/`
* accept reviewed drafts from `incoming/review/`
* add or adjust workflow behavior under `scripts/workflows/`
* regenerate `content/`, home/index pages, nav, or sidebar output
* run the local VitePress dev server or the local runtime image

This skill is an operational overlay, not the canonical repo policy.
Follow `AGENTS.md` first for repository rules, investigation order, generated-file boundaries, and command expectations.

## First Reads

When this skill is active, read in this order:

1. `AGENTS.md`
2. `README.md`
3. `docs/README.md`
4. `docs/authoring.md` when the task involves creating or editing content
5. `docs/cli.md` when the task involves cross-project authoring or installed CLI usage
6. `docs/skills.md` when the task involves globally installable Archive guidance for other agents
7. `Makefile`
8. `Containerfile.dev` and `Containerfile.runtime` if container behavior matters
9. `.vitepress/config.ts` if navigation or generated page structure may be involved
10. the relevant files under `scripts/`
11. `.agents/skills/archive-title-style/SKILL.md` when title cleanup matters

## Workflow Reminders

* the canonical flow is `incoming/ -> sources/ -> content/ -> site/`
* `sources/` is the only editable content root
* Archive supports standalone mode and private workspace mode
* in private workspace mode, canonical `incoming/` and `sources/` live under `WORKSPACE` while generated `content/`, `site/`, `build/`, and generated `.vitepress/*` output stay in the Archive tool repo
* `content/`, `site/`, `.vitepress/nav.generated.ts`, `.vitepress/sidebar.generated.ts`, and `.vitepress/knowledge/*.generated.json` are generated
* workflows are discovered from `scripts/workflows/*/workflow.yml`
* the repo currently ships `note` and `doc`, but more workflows may be added later
* source frontmatter may set `slug` for stable routes and `nav_title` for compact navigation labels
* source pages may keep page-local assets in sibling `<page-stem>.assets/` directories with ordinary relative Markdown links
* source pages may use plain ` ```mermaid ` fences; the local VitePress theme renders them client-side without manual Vue components in page content
* home, workflow indexes, top nav, and sidebar output follow non-empty workflows only
* the home page includes up to 10 recently added items from canonical sources
* local runtime uses a self-contained Caddy image built from `Containerfile.runtime`

## Command Mapping

Use these actions for common user requests:

* add a new canonical entry: run `make new kind=<workflow> title="..." section=...`, plus optional `slug=...`, `nav_title="..."`, `summary="..."`, `priority=...`, comma-separated `tags="a,b"`, comma-separated `related_manual="/x,/y"`, and hide flags like `hide_backlinks=1`
* bootstrap a private content repo: run `make WORKSPACE=/path/to/private/repo init-workspace`
* install the cross-project CLI: run `make install-cli`
* install the project-shipped global skill for other agents: run `make install-skill`
* process rough incoming files: run `make process-incoming`
* accept a reviewed draft: run `make accept-review file=incoming/review/...`
* validate canonical sources: run `make validate`
* regenerate generated Markdown, knowledge metadata, indexes, and nav/sidebar data: run `make build-content`
* build the static site: run `make build`
* run the foreground dev server: run `make dev`
* run the background dev server: run `make dev-bg`
* inspect or stop the background dev server: run `make dev-status`, `make dev-logs`, `make dev-stop`
* build the runtime image: run `make build` and then `make runtime-build`
* run or inspect the local runtime container: run `make runtime-run`, `make runtime-status`, `make runtime-logs`, `make runtime-stop`
* run full verification: run `make check`
* inspect repository health: run `make doctor`

## Content Editing Routing

When the user asks to update content:

* edit canonical Markdown in `sources/<workflow>/...`
* in private workspace mode, that canonical path is `WORKSPACE/sources/<workflow>/...`, not the Archive tool repo
* do not hand-edit `content/`, `site/`, `.vitepress/nav.generated.ts`, `.vitepress/sidebar.generated.ts`, or `.vitepress/knowledge/*.generated.json`
* when creating a new canonical page, prefer `make new` for scaffoldable metadata and keep `id`, `created`, `updated`, and default `status` system-managed
* keep canonical `section` paths lowercase and slash-separated; use `WORKSPACE/sources/<workflow>/_sections.yaml` for display labels like `OMV` or default sidebar collapse behavior
* keep page-local images and files in sibling `<page-stem>.assets/` directories under `sources/`; let `make build-content` copy them beside generated pages
* prefer plain ` ```mermaid ` fences in canonical Markdown instead of embedding manual Vue components for diagrams
* if the change is workflow-specific behavior, edit `scripts/workflows/<kind>/`
* if the change is shared generation behavior, edit `scripts/core/`
* if the change is orchestration or command wiring, edit `scripts/tasks/`, `scripts/runtime/`, `Makefile`, or container files as appropriate
* after source or workflow edits, rerun validation and the relevant build commands

## Workflow Creation Routing

When the user wants a new workflow:

* add a new folder under `scripts/workflows/<kind>/`
* include `workflow.yml`, `template.md`, `adapter.py`, `renderer.py`, and `validator.py`
* choose canonical roots under `sources/` and generated roots under `content/`
* keep workflow-specific rules out of `scripts/core/`
* verify the new workflow appears automatically once it has content

## Content Cleanup

When asked to improve a note or doc:

* keep edits focused unless the user asks for a rewrite
* fix spelling, grammar, and heading clarity
* preserve frontmatter structure and required workflow sections
* preserve explicit `slug` and `nav_title` unless the user wants route or navigation-label changes
* preserve code blocks unless the user asks otherwise
* use `.agents/skills/archive-title-style/SKILL.md` when title or heading cleanup is a major part of the task
