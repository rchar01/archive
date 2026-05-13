# Installable Skills

Archive ships a project-local installable skill for agents that work outside this repository.

`docs/skills.md` is the human install and usage page.
The skill file itself is the agent-facing source for cross-project Archive workflow behavior.

## Available Skill

- `archive-authoring`

Use it when an agent in another repo or directory still needs Archive-specific guidance for creating, importing, reviewing, validating, and building notes or docs.

The skill is intentionally stored under `skills/` instead of `.agents/skills/` so it is not auto-loaded from the project.
Install it manually when you want it globally available.

## Install

Install the skill globally:

```sh
make install-skill
```

Install into a custom global skill directory:

```sh
SKILLS_DIR=/path/to/skills make install-skill
```

Remove it later:

```sh
make uninstall-skill
```

## Recommended Pairing

For the best cross-project workflow, install both:

```sh
make install-cli
make install-skill
```

Use the split like this:

- humans inside a workspace repo: prefer the installed `archive` CLI
- agents working from other repos or arbitrary directories: prefer the installed `archive` CLI plus the `archive-authoring` skill

## Source of Truth

- `skills/archive-authoring/SKILL.md`: agent workflow behavior, guardrails, and command patterns
- `skills/archive-authoring/assets/`: command-choice guidance, exact generated note/doc scaffold references, metadata ownership notes, and `_sections.yaml` example overrides that install with the skill
- `docs/cli.md`: installed CLI behavior, workspace resolution, and command surface
- `docs/authoring.md`: canonical Archive authoring model, workflow-specific structure, and exact workflow-scoped `_sections.yaml` override paths for standalone and workspace modes
