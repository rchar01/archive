# AGENTS

This repository is an Archive workspace repo, not the main Archive tool repo.

## Purpose

- Canonical Archive content in this repo lives under `incoming/` and `sources/`.
- The Archive toolchain, build scripts, VitePress theme, and generated output live in the separate Archive repo referenced by `ARCHIVE_DIR` in `Makefile`.
- This workspace repo may be private or public.

## Use Available Specialist Tools

- If your runtime provides specialized tools or subagents for codebase exploration, use them when the repository structure or content location is unclear.
- If your runtime provides specialized tools or subagents for web research, use them when local repository sources are insufficient or when freshness matters.
- If your runtime provides specialized tools or subagents for verification, use them for targeted test runs, build checks, or command-heavy validation.
- If your runtime provides specialized tools or subagents for review, use them after substantial edits to catch regressions, missing updates, or doc/code drift.
- Prefer local repository docs, scripts, and configuration first.
- If the global `archive-authoring` skill is available, use it for Archive-specific authoring rules and command routing.

## Local Working Model

- `incoming/new/`: rough draft intake
- `incoming/review/`: normalized drafts waiting for approval
- `sources/notes/`: canonical note sources
- `sources/docs/`: canonical doc sources
- Use the forwarding `Makefile` in this repo as the default interface.
- By default, that `Makefile` forwards to `../archive`.
- Override the Archive repo location with `ARCHIVE_DIR=...` if needed.
- Do not assume the installed `archive` CLI is available in this repo.

## Commands To Use Here

- `make help`
- `make validate`
- `make build`
- `make check`
- `make new kind=note title="DNS Notes" section=infra`
- `make process-incoming`
- `make accept-review file=incoming/review/...`

## Editing Boundaries

- Edit canonical Markdown in `sources/`.
- Put rough imported Markdown in `incoming/new/` and process it through the intake flow.
- Do not hand-edit generated output such as `content/`, `site/`, or generated `.vitepress/*` files; those belong to the Archive tool repo workflow, not this repo.

## Minimal Content Rules

- Keep the required first workflow section intact: `## Overview` for docs and `## Summary` for notes.
- Keep `section` lowercase and slash-separated, for example `homelab/omv`.
- When structure or metadata conventions are unclear, do not guess. Use the Archive repo docs or the `archive-authoring` skill if available.

## Source of Truth

- Prefer executable behavior over prose if they disagree.
- For fuller Archive authoring rules, use the `archive-authoring` skill if available or read the Archive repo docs:
  - `docs/authoring.md`
  - `docs/note.md`
  - `docs/doc.md`

## Verification

- After content edits, run `make validate`.
- Before finishing substantial work, run `make build` or `make check`.
