# Archive Workspace

This repository stores canonical Archive content in a separate repo.
It may be private or public.

## Layout

- `incoming/new/`: rough draft intake
- `incoming/review/`: normalized drafts waiting for approval
- `sources/notes/`: canonical notes
- `sources/docs/`: canonical docs

Generated `content/`, `site/`, and `.vitepress/*generated*` output stay in the Archive tool clone.
This bootstrap stays intentionally empty; the public repo's optional `examples/` starter content is not copied into the workspace repo.

## Usage

Set `ARCHIVE_DIR` in the forwarding `Makefile` if your Archive clone is not at `../archive`.

Then run commands from this workspace repo:

```sh
make validate
make new kind=note title="DNS Notes" section=infra
make build
```

Those commands forward to Archive with `WORKSPACE=$(CURDIR)`.
Use this forwarding `Makefile` as the default interface when you are already inside the workspace repo.
The installed `archive` CLI is optional and is most useful for cross-project or external-agent workflows.
