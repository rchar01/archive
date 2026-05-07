# Command Choice

Use this quick rule set when choosing Archive commands.

## Use `archive new`

Use `archive new` when:

- you are creating a brand-new canonical page from scratch
- you already know the workflow (`note` or `doc`)
- you already know the target `section`
- you want the standard scaffold with system-managed frontmatter and the required first heading

Do not use `archive new` first when the starting point is already a rough Markdown file that needs AI cleanup or normalization.

## Use `archive import`

Use `archive import` when:

- you already have a rough Markdown file
- the content came from another repo, notes app, or AI output
- the content needs Archive frontmatter added or normalized
- the content may need workflow-specific reshaping before it becomes canonical

Typical pattern:

```sh
archive import /path/to/raw.md --workspace /path/to/repo --kind note --section homelab/omv --processing review
```

## Use `archive process`

Use `archive process` after files have been staged into `incoming/new/`.

`archive process`:

- normalizes rough intake through the workflow adapter
- writes directly to `sources/...` when `processing: auto`
- writes a normalized draft to `incoming/review/...` when `processing: review`

## Use `archive accept`

Use `archive accept` only after a review-gated draft already exists in `incoming/review/` and should become canonical content in `sources/...`.

## Quick Decision Rule

- brand-new page from scratch: `archive new`
- existing rough Markdown that AI should reshape: `archive import` -> `archive process`
- reviewed draft ready to become canonical: `archive accept`
- already canonical note or doc in `sources/...` that needs reformatting or cleanup: edit the existing canonical file directly, then validate/build as needed

Do not use `archive new` to reformat a page that already exists in `sources/...`.

Source of truth:

- `scripts/cli/archive.py`
- `docs/authoring.md`
