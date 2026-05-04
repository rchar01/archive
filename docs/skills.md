# Installable Skills

Archive ships a project-local installable skill for agents that work outside this repository.

## Available Skill

- `archive-authoring`

Use it when an agent in another repo or directory still needs to:

- create new Archive notes or docs
- import raw Markdown into Archive intake
- process and accept review drafts
- validate and build an Archive workspace

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

- humans inside a private workspace repo: prefer the generated forwarding `Makefile`
- agents working from other repos or arbitrary directories: prefer the installed `archive` CLI plus the `archive-authoring` skill
