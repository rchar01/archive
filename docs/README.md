# Documentation

Human-facing documentation for Archive lives here.

- [Installed CLI](cli.md) - install and use the `archive` command, workspace discovery, bootstrap behavior, and command surface.
- [Authoring Workflow](authoring.md) - create, import, review, validate, preview, and build canonical notes and docs.
- [Workspace Mode](workspace.md) - split workspace/tool-repo ownership, workspace bootstrap, optional forwarding `Makefile`, and local preview/runtime use.
- [Workspace CI](workspace-ci.md) - pinned Archive checkout, static-site build, runtime image packaging, and deployment pattern.
- [Note Workflow](note.md) - note-specific source root, required sections, metadata helpers, assets, Mermaid, and validation rules.
- [Doc Workflow](doc.md) - doc-specific source root, required sections, metadata helpers, assets, Mermaid, and validation rules.
- [Installable Skills](skills.md) - install and use the cross-project `archive-authoring` skill for agents.

The root `README.md` is intentionally a quick start and repository overview. These docs are the source of truth for human and agent workflows.

Bundled third-party asset notices live in [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). Skill sources live in [`../skills/`](../skills/) and are installed with `make install-skill`.
