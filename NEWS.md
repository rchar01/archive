# News

This file gives a short, release-oriented view of what changed between versions.

## v1.5.0 - 2026-05-10

- added Archive logo and favicon assets with light and dark variants, using tool-owned static assets under `.vitepress/public/brand/`
- added Phosphor Icons attribution and a reusable `512x512` forge avatar asset
- tightened auto-related suggestions so unrelated pages no longer appear related solely because they share a section like `dev`
- filtered generated index-section hits out of plain-text local search so results more consistently open real note/doc pages with matching sidebar state, while explicit tag searches still include tag pages

## v1.4.0 - 2026-05-10

- upgraded the site build to pinned VitePress `2.0.0-alpha.17`, bringing in the Vite 7, Shiki 3, MiniSearch 7, and DocSearch 4 dependency surface
- refreshed the npm lockfile for the VitePress 2 alpha dependency tree and cleared the transitive `uuid` audit finding through `mermaid`

## v1.3.0 - 2026-05-09

- added `ARCHIVE_INSTANCE`-scoped generated output so one Archive clone can build, preview, and package multiple workspaces concurrently without collisions
- added generated tag pages plus clickable Context-panel tags so tags are navigable in the published site instead of metadata-only
- added local-search tag queries like exact `#proxmox`, prefix `#proxm*`, and tag-qualified text queries like `#proxmox network`, which return page-level results for matching generated tag pages and explicitly tagged pages while leaving plain text search unchanged
- added destination-page search highlighting so terms selected from local-search results stay highlighted on the opened page, including matches inside code blocks and code language labels
- made workspace bootstrap refreshes safer and easier by keeping `init-workspace` non-destructive by default while supporting explicit root-template refreshes with `FORCE=1` or `archive init-workspace --force`
- refreshed the top-level README and workspace docs to explain what Archive adds beyond plain VitePress and how instance-aware workspace mode works

## v1.2.1 - 2026-05-07

- bumped the pinned `PyYAML` dependency from `6.0.2` to the current stable `6.0.3`
- left `vitepress` at `1.6.4` and `mermaid` at `11.14.0` because both are already on their latest stable releases

## v1.2.0 - 2026-05-07

- simplified canonical body structure so `note` requires only `Summary` and `doc` requires only `Overview`
- stopped scaffolding and intake normalization from auto-inserting `## Details`, while still allowing later major `##` sections when the page needs them
- normalized manual thematic breaks like `---`, `***`, and `___` immediately before `##` headings so generated pages do not show duplicate separators alongside the default VitePress section divider
- updated agent skills, authoring docs, and examples to teach the new heading model and separator rule

## v1.1.0 - 2026-05-04

- added an installed `archive` CLI for cross-project authoring, raw Markdown import, intake processing, review acceptance, validation, and builds against standalone mode or workspace mode
- added a project-shipped `archive-authoring` skill plus install/uninstall helpers so agents outside this repo can learn the Archive workflow explicitly
- made `note` and `doc` body structure less rigid by requiring only `Summary` for notes and `Overview` for docs while leaving `Related`, `References`, and any later major `##` sections optional
- clarified that workspace repos should keep using the forwarding `Makefile` for local human usage while external agents can use the installed CLI
- fixed the generated workspace forwarding `Makefile` so plain `make` correctly forwards to Archive help instead of becoming a no-op

## v1.0.0 - 2026-04-29

Archive 1.0.0 is the first public release of the source-first documentation system.

- introduced the canonical `incoming/ -> sources/ -> content/ -> site/` workflow for rough intake, editable source content, generated VitePress input, and generated static output
- shipped dynamic workflow discovery with built-in `note` and `doc` workflows, plus workflow-local templates, adapters, renderers, and validators
- added generated navigation, workflow indexes, recent-content home sections, and a repo-local knowledge panel powered by generated page, linkgraph, and related metadata
- added authoring helpers for `slug`, `nav_title`, `summary`, tags, curated related links, and page-level knowledge-panel visibility flags
- added support for sibling `<page-stem>.assets/` source asset folders and plain Markdown Mermaid fences rendered by the local VitePress theme
- documented the two supported operating modes: standalone Archive and the recommended tooling-plus-workspace split
- added workspace bootstrap guidance, wrapper `Makefile` docs, pinned workspace CI packaging guidance, and a `docs/` reference set for human-facing documentation
- shipped a tiny optional starter corpus under `sources/**/examples/` so first-run standalone builds show real content, assets, Mermaid rendering, and knowledge-panel links
- shipped containerized development and runtime flows with `make` targets for validation, content generation, preview, static builds, and local runtime serving
- removed legacy archive pipeline structure in favor of the current `scripts/core/`, `scripts/workflows/`, `scripts/tasks/`, and `scripts/runtime/` architecture
