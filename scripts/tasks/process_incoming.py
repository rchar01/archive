from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.frontmatter import read_markdown, write_markdown
from scripts.core.paths import relative_to_workspace, resolve_workspace_path
from scripts.core.registry import get_workflow
from scripts.core.reports import write_json_report
from scripts.core.slug import slugify
from scripts.core.validation import require_choice, require_field


def incoming_files(incoming_dir: Path) -> list[Path]:
    return sorted(path for path in incoming_dir.glob("*.md") if path.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="incoming/new")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    incoming_dir = resolve_workspace_path(Path(args.path))
    review_dir = incoming_dir.parent / "review"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, str]] = []
    for path in incoming_files(incoming_dir):
        document = read_markdown(path)
        kind = str(require_field(document.frontmatter, "kind")).strip()
        workflow = get_workflow(kind)
        processing = str(document.frontmatter.get("processing") or "auto").strip() or "auto"
        require_choice(processing, ["auto", "review"], "processing")

        adapter = workflow.load_module("adapter")
        normalized = adapter.from_incoming(document, default_section=workflow.default_section)
        title = str(require_field(normalized.frontmatter, "title")).strip()
        section = str(require_field(normalized.frontmatter, "section")).strip()

        if processing == "review":
            target = review_dir / f"{slugify(title)}.md"
        else:
            target = workflow.source_path_for(title, section)

        if target.exists() and not args.force:
            raise SystemExit(f"Refusing to overwrite existing file: {relative_to_workspace(target)}")

        write_markdown(target, normalized)
        path.unlink()
        results.append(
            {
                "source": relative_to_workspace(path),
                "target": relative_to_workspace(target),
                "processing": processing,
                "kind": kind,
            }
        )

    write_json_report("process-incoming", {"entries": results})
    print(f"Processed {len(results)} incoming files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
