from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.frontmatter import read_markdown, write_markdown
from scripts.core.paths import relative_to_workspace, resolve_workspace_path
from scripts.core.registry import get_workflow
from scripts.core.validation import require_field


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    review_path = resolve_workspace_path(Path(args.file))
    document = read_markdown(review_path)
    kind = str(require_field(document.frontmatter, "kind")).strip()
    title = str(require_field(document.frontmatter, "title")).strip()
    section = str(require_field(document.frontmatter, "section")).strip()
    workflow = get_workflow(kind)
    target = workflow.source_path_for(title, section)

    if target.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {relative_to_workspace(target)}")

    write_markdown(target, document)
    review_path.unlink()
    print(relative_to_workspace(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
