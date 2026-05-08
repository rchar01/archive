# Documentation

This directory contains the human-facing documentation for Archive.

The repository currently ships these workflows:

- `note`
- `doc`

Workflow configuration is machine-readable and discovered from `scripts/workflows/*/workflow.yml`.

Additional workflows can be added later without changing central registry files.

Non-empty workflows appear automatically in generated home navigation, top navigation, workflow indexes, and sidebar output.

These files explain the supported usage modes, authoring flow, and workflow-specific rules.

Recommended reading order:

- `cli.md` for the installed cross-project command wrapper
- `skills.md` for the manually installable cross-project Archive skill
- `authoring.md` for the end-to-end human and agent authoring workflow
- `note.md` for note-specific structure and constraints
- `doc.md` for doc-specific structure and constraints
- `workspace.md` for the split tooling/workspace-repo model
- `workspace-ci.md` for the recommended workspace CI and deployment pattern
