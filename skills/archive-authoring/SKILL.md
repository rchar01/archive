---
name: archive-authoring
description: Use the installed `archive` CLI to create, import, review, validate, and build Archive notes/docs from other repositories or directories.
compatibility: opencode
metadata:
  audience: all-users
  workflow: cross-project-authoring
  domain: publishing
---

# Archive Authoring

## Purpose

Use this skill when an agent is not working inside the Archive repository but still needs to operate on Archive content in a standalone repo or a private workspace.

Prefer the installed `archive` CLI over raw `make -C ... WORKSPACE=...` commands.
Treat this skill as the agent-facing source for cross-project Archive workflow behavior.

## Prerequisites

Install the `archive` CLI and this skill from the Archive repository.

Recommended commands from the Archive repo:

```sh
make install-cli
make install-skill
```

The default global skill target is `~/.agents/skills/archive-authoring`.

## Core Model

- `sources/` is the canonical editable content root
- `content/`, `site/`, generated nav/sidebar data, and generated knowledge metadata are machine-owned output
- Archive supports two modes:
  - standalone repo
  - private workspace with canonical `incoming/` and `sources/` in a separate repo
- the installed `archive` CLI can infer `--workspace` when run inside a valid Archive workspace
- when run elsewhere, pass `--workspace /path/to/repo`

## Workflow Choice

- use `note` for smaller atomic entries
- use `doc` for larger articles, guides, references, and architecture pages
- keep canonical `section` paths lowercase and slash-separated such as `homelab/security` or `kubernetes/omv`

Required sections:

- `note`: `Summary`, `Details`
- `doc`: `Overview`, `Details`

Optional sections:

- `note`: `Related`
- `doc`: `References`

## Canonical Flow

```text
incoming/ -> sources/ -> content/ -> site/
```

## Common Commands

Create a canonical page directly:

```sh
archive new note --title "DNS Notes" --section infra
archive new doc --title "Homelab Firewall" --section homelab/networking
```

Import a raw Markdown file from another location into the intake queue:

```sh
archive import /path/to/raw.md --workspace /path/to/repo --kind doc --section inbox --processing review
```

Normalize intake and accept a reviewed draft:

```sh
archive process --workspace /path/to/repo
archive accept incoming/review/raw.md --workspace /path/to/repo
```

Validate and build:

```sh
archive validate --workspace /path/to/repo
archive build --workspace /path/to/repo
archive check --workspace /path/to/repo
```

## Authoring Rules

- do not hand-edit generated files under `content/`, `site/`, or generated `.vitepress/*`
- keep page-local assets in sibling `<page-stem>.assets/` directories beside the canonical source page
- plain ` ```mermaid ` fences are supported in canonical Markdown
- preserve explicit `slug` and `nav_title` unless the user asks to change routes or navigation labels
- use workflow-local `_sections.yaml` files under `sources/docs/` or `sources/notes/` to override displayed section labels such as `OMV` or default sidebar fold state
- use `processing: review` for rough or AI-generated imports that should be inspected before acceptance

Example section overrides:

```yaml
sections:
  homelab:
    title: Homelab
    collapsed: false

  homelab/omv:
    title: OMV
    collapsed: true
```

## Human vs Agent UX

- inside a private workspace repo, humans should usually keep using the generated forwarding `Makefile`
- agents working from other directories or other repositories should use the installed `archive` CLI
