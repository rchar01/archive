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

- `note`: `Summary`
- `doc`: `Overview`

Optional sections:

- `note`: `Related`
- `doc`: `References`

## Writing Model

- one page should have one `#` heading only
- keep required workflow headings as `##` sections
- add more `##` headings after `Summary` or `Overview` for major sections when the page needs them
- do not place manual thematic breaks like `---`, `***`, or `___` immediately before a `##` heading; use the `##` heading itself as the section boundary
- use `###` for real subsections under those major `##` sections
- prefer small focused pages over one page that mixes unrelated topics

Use `note` when the content is:

- atomic
- reusable
- one problem, finding, command set, or concept
- easy to link from other pages

Use `doc` when the content is:

- a guide
- a reference page
- an architecture explanation
- a larger workflow with multiple subsections

Writing guidance for required sections:

- `Summary` in a note should state the takeaway quickly in 1-3 short paragraphs or bullets
- `Overview` in a doc should explain what the page covers and when to use it
- after `Summary` or `Overview`, add additional `##` headings for the real major sections of the page
- `Details` is optional and works as a generic fallback when a rough imported draft does not already have clearer major headings
- add `Related` only when you want explicit in-body links beyond the generated knowledge panel
- add `References` only when the page has real source material or canonical external references worth preserving

## Splitting Pages

Split one page into multiple pages when:

- sections answer different questions
- sections would be useful as standalone links
- one page mixes guide, reference, troubleshooting, and notes without a single through-line
- the title feels like two or more topics joined together

Keep one page when:

- the content serves one task or one topic
- subsections are steps or parts of the same explanation
- readers benefit from reading it in one place end to end

## Linking and Knowledge Graph

- link directly to other Archive pages in the body when the text naturally references them
- use internal Archive links such as `/docs/...` or `/notes/...`
- backlinks are generated automatically from those internal links; do not hand-maintain backlink sections
- auto-related suggestions are generated from metadata and linking patterns
- use `related_manual` when a page should appear as related even if the body does not naturally link to it
- do not use `related_manual` as a substitute for normal in-body links when a direct reference belongs in the prose

Use this pattern:

- body link: when the current sentence or step directly depends on another page
- `related_manual`: when two pages are strongly associated but the body does not need an inline link

## Metadata Guidance

- keep `section` lowercase and slash-separated
- use `slug` when you want a stable short route
- use `nav_title` when the full `title` is too long for sidebar and index display
- use `summary` when you want tighter control over generated previews
- use tags for lightweight categorization, not as a substitute for clear sections or links
- preserve explicit `slug` and `nav_title` unless the user asks to change routes or navigation labels

Exact helper-generated scaffold references shipped with this skill:

- `assets/command-choice.md`
- `assets/generated-note.md`
- `assets/generated-doc.md`
- `assets/metadata-reference.md`
- `assets/sections.example.yaml`

If these references ever conflict with repository code, treat the repository templates and `scripts/tasks/new_entry.py` as canonical.

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

## When to Use What

- use `archive new` when creating a brand-new canonical page from scratch and you already know the workflow and target `section`
- use `archive import` when the starting point is already a rough Markdown file, imported note, or AI-generated draft that should be normalized into Archive format
- use `archive process` after files are in `incoming/new/`; it normalizes the intake and either writes directly to `sources/...` for `processing: auto` or stages a normalized draft in `incoming/review/...` for `processing: review`
- use `archive accept` only after a review-gated draft already exists in `incoming/review/...` and should become canonical content
- if the page already exists in `sources/...`, edit that canonical file directly instead of using `archive new`, `archive import`, or `archive accept`
- do not run `archive new` first for rough incoming content that needs cleanup; use `archive import` followed by `archive process` instead
- see `assets/command-choice.md` for the compact decision guide

Validate and build:

```sh
archive validate --workspace /path/to/repo
archive build --workspace /path/to/repo
archive check --workspace /path/to/repo
```

## Authoring Rules

- do not hand-edit generated files under `content/`, `site/`, or generated `.vitepress/*`
- do not manually create section directories under `sources/` when using normal Archive authoring flows; `archive new` and `archive process` create missing parent directories automatically
- prefer `archive new ...` for direct canonical pages and `archive process ...` for intake normalization instead of hand-creating `sources/<workflow>/<section>/`
- keep page-local assets in sibling `<page-stem>.assets/` directories beside the canonical source page
- reference local assets with ordinary relative Markdown paths such as `![Topology](./firewall.assets/topology.svg)`
- plain ` ```mermaid ` fences are supported in canonical Markdown
- preserve explicit `slug` and `nav_title` unless the user asks to change routes or navigation labels
- do not place manual thematic breaks like `---`, `***`, or `___` immediately before a `##` heading; Archive normalizes those away because VitePress already renders a section divider for `##`
- use workflow-local `_sections.yaml` files to override displayed section labels such as `OMV` or default sidebar fold state
- exact paths are workflow-scoped:
  - standalone mode: `sources/docs/_sections.yaml` and `sources/notes/_sections.yaml`
  - private workspace mode: `WORKSPACE/sources/docs/_sections.yaml` and `WORKSPACE/sources/notes/_sections.yaml`
- docs and notes are independent; if you want `OMV` only for docs, change only the docs file, and if you want it in both workflows, add the override to both files
- use `processing: review` for rough or AI-generated imports that should be inspected before acceptance

Example section overrides are also bundled in `assets/sections.example.yaml`:

```yaml
sections:
  homelab:
    title: Homelab
    collapsed: false

  homelab/omv:
    title: OMV
    collapsed: true
```

If no matching override exists, Archive falls back to auto-humanized labels, so a canonical section path like `homelab/omv` displays as `Omv`.

## Examples

Minimal note:

```md
---
title: Docker DNS Issue
kind: note
section: containers
tags:
  - docker
  - dns
related_manual:
  - /docs/networking/dns-basics
---

# Docker DNS Issue

## Summary

Containers can reach raw IPs but fail DNS lookups because the resolver path is broken.

### Symptoms

- container can `ping 1.1.1.1`
- container cannot resolve hostnames

### Fix

Check the Docker daemon DNS settings and compare them with `/etc/resolv.conf` on the host.

See [/docs/networking/dns-basics](/docs/networking/dns-basics) for the resolver model.
```

Minimal doc:

```md
---
title: Homelab Firewall
kind: doc
section: homelab/networking
slug: edge-firewall
nav_title: Edge Firewall
summary: Firewall overview and operating notes.
tags:
  - firewall
  - homelab
  - networking
---

# Homelab Firewall

## Overview

This page explains the firewall role, network position, and the main operating rules for the homelab edge.

## Topology

Describe interfaces, zones, and traffic expectations.

## Operating Rules

List the rules that should remain true during changes and troubleshooting.

## Related Pages

See [/docs/homelab/security/homelab-https-setup](/docs/homelab/security/homelab-https-setup) for the HTTPS side of the same environment.
```

## Human vs Agent UX

- inside a private workspace repo, humans should usually keep using the generated forwarding `Makefile`
- agents working from other directories or other repositories should use the installed `archive` CLI
