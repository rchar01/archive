---
name: archive-title-style
description: Apply title-case-guide to archive notes, headings, slugs, and title cleanup tasks.
depends:
  - title-case-guide
---

# Purpose

Use `title-case-guide` during archive title and heading maintenance.

# What To Edit

- frontmatter `title`
- frontmatter `nav_title` when a shorter navigation label is needed
- frontmatter `slug` only when the route should intentionally change or be stabilized
- top headings
- duplicate heading/title echoes

# Cleanup Rules

Also fix:

- obvious spelling mistakes
- weak or raw capture phrasing
- noisy shorthand titles

# Guardrails

- do not change dates
- preserve note meaning
- keep archival references stable unless asked
- do not change explicit `slug` just because `title` changes unless the user wants the route changed too
