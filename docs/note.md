# Note Workflow

## Purpose

Use `note` for small, atomic, reusable knowledge entries.

For the full end-to-end authoring flow, including when to use `make new` versus `incoming/new`, see `docs/authoring.md`.

## Canonical Source Root

- `WORKSPACE/sources/notes/`

## Generated Output Root

- `ARCHIVE_TOOL_ROOT/content/notes/`

## Required Sections

- `Summary`

`Related` is optional. Add it only when you want explicit in-body links beyond the generated knowledge panel.
Add more `##` headings after `Summary` when the note needs structure. `## Details` is optional and works as a generic fallback when a rough imported note has no clearer major sections yet.
Do not place manual thematic breaks like `---`, `***`, or `___` immediately before a `##` heading; use the heading itself as the section boundary.

## Intake Rules

- incoming files must declare `kind: note`
- `processing: auto` writes directly to `WORKSPACE/sources/notes/...`
- `processing: review` writes to `WORKSPACE/incoming/review/...`

## Common Metadata Helpers

- `make new` can scaffold `slug`, `nav_title`, `summary`, `priority`, comma-separated `tags`, comma-separated `related_manual`, and knowledge-panel hide flags
- `id`, `created`, `updated`, and default `status: draft` remain system-managed
- use `slug` for stable short routes and `nav_title` for compact navigation labels when needed
- keep `section` lowercase and slash-separated; use `WORKSPACE/sources/notes/_sections.yaml` for display labels or default sidebar fold state

Example `_sections.yaml`:

```yaml
sections:
  homelab:
    title: Homelab
    collapsed: false

  homelab/omv:
    title: OMV
    collapsed: true
```

## Ownership

- source template, adapter, renderer, and validator live in `scripts/workflows/note/`

## Local Assets

- keep page-local images in a sibling `<page-stem>.assets/` directory next to the canonical source file
- reference them with ordinary relative Markdown paths such as `![Diagram](./network-trace.assets/flow.svg)`
- the build copies that asset directory beside the generated page in `content/`
- if the page sets `slug`, the generated page filename uses the slug while the copied asset directory keeps the source file stem

## Mermaid

- note pages may use plain ` ```mermaid ` fences in canonical Markdown
- the local VitePress theme renders Mermaid client-side; do not replace those fences with manual Vue components in page content

## Validate and Preview

- run `make validate` after editing canonical notes
- run `make build` for a full rebuild or `make dev-bg` for a local preview loop
- in workspace mode, run those commands from the workspace repo wrapper `Makefile` or from the Archive repo with `WORKSPACE=/path/to/workspace`
