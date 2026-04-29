# News

This file gives a short, release-oriented view of what changed between versions.

## v1.0.0 - 2026-04-29

Archive 1.0.0 is the first public release of the source-first documentation system.

- introduced the canonical `incoming/ -> sources/ -> content/ -> site/` workflow for rough intake, editable source content, generated VitePress input, and generated static output
- shipped dynamic workflow discovery with built-in `note` and `doc` workflows, plus workflow-local templates, adapters, renderers, and validators
- added generated navigation, workflow indexes, recent-content home sections, and a repo-local knowledge panel powered by generated page, linkgraph, and related metadata
- added authoring helpers for `slug`, `nav_title`, `summary`, tags, curated related links, and page-level knowledge-panel visibility flags
- added support for sibling `<page-stem>.assets/` source asset folders and plain Markdown Mermaid fences rendered by the local VitePress theme
- documented the two supported operating modes: standalone Archive and the recommended public-tooling plus private-workspace split
- added private workspace bootstrap guidance, wrapper `Makefile` docs, pinned private CI packaging guidance, and a `docs/` reference set for human-facing documentation
- shipped a tiny optional starter corpus under `sources/**/examples/` so first-run standalone builds show real content, assets, Mermaid rendering, and knowledge-panel links
- shipped containerized development and runtime flows with `make` targets for validation, content generation, preview, static builds, and local runtime serving
- removed legacy archive pipeline structure in favor of the current `scripts/core/`, `scripts/workflows/`, `scripts/tasks/`, and `scripts/runtime/` architecture
