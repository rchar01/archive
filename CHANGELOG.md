# Changelog

All notable changes to `archive` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-04

### Added

- an installed `archive` CLI with `init-workspace`, `new`, `import`, `process`, `accept`, `validate`, `build-content`, `build`, and `check` commands for cross-project usage
- `make install-cli` plus `scripts/install-cli` to install the user-facing `archive` command into `~/.local/bin` by default
- a project-shipped `archive-authoring` skill under `skills/` for agents outside this repo, plus `make install-skill`, `make uninstall-skill`, `scripts/install-skill`, and `scripts/uninstall-skill`
- `docs/cli.md` and `docs/skills.md` documenting the installed CLI and manually installable cross-project skill
- CLI and skill surface tests covering workspace inference, raw import staging, installer behavior, and skill install/uninstall flows

### Changed

- made `note` require only `Summary`, with `Related` and later major `##` sections optional
- made `doc` require only `Overview`, with `References` and later major `##` sections optional
- stopped scaffolding and intake-normalization from auto-generating empty trailing `Related` and `References` sections
- updated private-workspace docs and template guidance to keep `make` as the default interface inside the private repo while reserving the installed CLI for cross-project and external-agent workflows

### Fixed

- the generated private-workspace forwarding `Makefile` now forwards plain `make` to Archive help instead of resolving to an empty local `help` target

## [1.0.0] - 2026-04-29

### Added

- source-first publishing flow with canonical content in `sources/` and generated output in `content/` and `site/`
- dynamic workflow discovery from `scripts/workflows/*/workflow.yml`
- built-in `note` and `doc` workflows with workflow-local templates, adapters, renderers, validators, and defaults
- generated home page, workflow index pages, top navigation, sidebar data, and recent-content sections
- repo-local knowledge panel backed by generated page catalog, linkgraph, and related-content metadata
- `make new`, `make process-incoming`, and `make accept-review` flows for direct authoring, rough intake, and review-gated intake
- optional frontmatter support for `slug`, `nav_title`, `summary`, `priority`, `related_manual`, `hide_knowledge_panel`, `hide_backlinks`, and `hide_related`
- support for sibling `<page-stem>.assets/` source asset folders copied beside generated pages
- Mermaid support for plain Markdown ` ```mermaid ` fences rendered by the local VitePress theme
- local dev and runtime container flows via `make dev`, `make dev-bg`, `make build`, `make runtime-build`, and `make runtime-run`
- repository health and validation surfaces via `make validate`, `make check`, and `make doctor`
- `make init-workspace` bootstrap flow and private-workspace template files for private content repositories
- `docs/private-workspace.md` and `docs/private-ci.md` documenting the split public-tooling/private-content operating model and pinned private CI flow
- a small optional starter corpus under `sources/notes/examples/` and `sources/docs/examples/` for first-run standalone usage

### Changed

- standardized the repository around `incoming/`, `sources/`, `content/`, `site/`, `scripts/core/`, `scripts/workflows/`, `scripts/tasks/`, and `scripts/runtime/`
- moved related-links and backlink presentation out of generated Markdown bodies and into the VitePress theme layer
- made generated routes slug-aware and navigation labels `nav_title`-aware while preserving full canonical page titles in page bodies
- updated authoring docs to describe direct canonical authoring, intake/review flows, local assets, Mermaid usage, and validation/build loops
- documented standalone mode, private workspace mode, wrapper `Makefile` usage, generated-output ownership, and prebuilt-site runtime packaging under `docs/`

### Fixed

- duplicate output-path validation for pages that would otherwise resolve to the same generated route
- frontmatter preservation and validation for knowledge-panel controls and routing/navigation metadata
- SSR-safe Mermaid rendering with rerendering on route navigation and dark/light mode changes
- generated asset copying for source-local `<page-stem>.assets/` directories
