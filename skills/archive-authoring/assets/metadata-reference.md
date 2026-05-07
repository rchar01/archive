# Metadata Reference

## System-managed fields

The helper script manages these fields:

- `id`
- `created`
- `updated`
- default `status: draft`

Agents should preserve these unless the user explicitly asks to change them and the workflow supports that change.

## Common author-controlled fields

- `title`
- `section`
- `slug`
- `nav_title`
- `summary`
- `priority`
- `tags`
- `related_manual`
- `hide_knowledge_panel`
- `hide_backlinks`
- `hide_related`

## Notes

- `section` should stay lowercase and slash-separated.
- `slug` should use lowercase letters, numbers, and hyphens only.
- `nav_title` is for compact navigation labels; `title` remains the full canonical page title.
- `tags` and `related_manual` are scaffolded from comma-separated input.

Source of truth:

- `scripts/tasks/new_entry.py`
- `docs/authoring.md`
