# Doc Workflow

## Purpose

Use `doc` for structured documentation pages.

For the full end-to-end authoring flow, including when to use `make new` versus `incoming/new`, see `docs/authoring.md`.

## Canonical Source Root

- `WORKSPACE/sources/docs/`

## Generated Output Root

- `ARCHIVE_TOOL_ROOT/content/docs/`

## Required Sections

- `Overview`
- `Details`
- `References`

## Intake Rules

- incoming files must declare `kind: doc`
- `processing: auto` writes directly to `WORKSPACE/sources/docs/...`
- `processing: review` writes to `WORKSPACE/incoming/review/...`

## Common Metadata Helpers

- `make new` can scaffold `slug`, `nav_title`, `summary`, `priority`, comma-separated `tags`, comma-separated `related_manual`, and knowledge-panel hide flags
- `id`, `created`, `updated`, and default `status: draft` remain system-managed
- use `slug` for stable short routes and `nav_title` for compact navigation labels when needed

## Ownership

- source template, adapter, renderer, and validator live in `scripts/workflows/doc/`

## Local Assets

- keep page-local images in a sibling `<page-stem>.assets/` directory next to the canonical source file
- reference them with ordinary relative Markdown paths such as `![Topology](./firewall.assets/topology.svg)`
- the build copies that asset directory beside the generated page in `content/`
- if the page sets `slug`, the generated page filename uses the slug while the copied asset directory keeps the source file stem

## Mermaid

- doc pages may use plain ` ```mermaid ` fences in canonical Markdown
- the local VitePress theme renders Mermaid client-side; do not replace those fences with manual Vue components in page content

## Validate and Preview

- run `make validate` after editing canonical docs
- run `make build` for a full rebuild or `make dev-bg` for a local preview loop
- in private workspace mode, run those commands from the private repo wrapper `Makefile` or from the Archive repo with `WORKSPACE=/path/to/private/repo`
