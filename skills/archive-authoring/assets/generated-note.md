# Generated Note Scaffold

This is the exact base note scaffold produced by the helper template before optional author-controlled metadata like `slug`, `nav_title`, `summary`, `priority`, `related_manual`, and knowledge-panel flags are added.

```md
---
id: "<generated id>"
title: "<title>"
kind: "note"
section: "<normalized/lowercase/section/path>"
status: "draft"
tags: []
created: "<YYYY-MM-DD>"
updated: "<YYYY-MM-DD>"
---

# <title>

## Summary
```

Source of truth:

- `scripts/workflows/note/template.md`
- `scripts/tasks/new_entry.py`
