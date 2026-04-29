from __future__ import annotations

from datetime import datetime, timezone
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.content_writer import write_generated_markdown
from scripts.core.frontmatter import read_markdown
from scripts.core.markdown import markdown_files
from scripts.core.paths import relative_to_tool, relative_to_workspace
from scripts.core.registry import discover_workflows
from scripts.core.reports import write_json_report
from scripts.core.validation import require_field, require_optional_slug


def adjacent_asset_dir(path: Path) -> Path:
    return path.with_name(f"{path.stem}.assets")


def copy_adjacent_assets(source_path: Path, output_path: Path) -> None:
    source_assets = adjacent_asset_dir(source_path)
    if not source_assets.is_dir():
        return
    output_assets = output_path.with_name(source_assets.name)
    shutil.copytree(source_assets, output_assets, dirs_exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    workflows = discover_workflows()
    entries: list[dict[str, str]] = []

    for workflow in workflows.values():
        shutil.rmtree(workflow.output_root, ignore_errors=True)

    for workflow in workflows.values():
        renderer = workflow.load_module("renderer")
        validator = workflow.load_module("validator")
        for path in markdown_files(workflow.source_root):
            document = read_markdown(path)
            validator.validate(document, required_sections=workflow.required_sections)
            title = str(require_field(document.frontmatter, "title")).strip()
            section = str(require_field(document.frontmatter, "section")).strip()
            slug = require_optional_slug(document.frontmatter, "slug")
            output_path = workflow.output_path_for(title, section, slug=slug)
            page = renderer.render(document, source_path=path, output_path=output_path)
            write_generated_markdown(page)
            copy_adjacent_assets(path, output_path)
            entries.append(
                {
                    "kind": workflow.kind,
                    "source": relative_to_workspace(path),
                    "output": relative_to_tool(output_path),
                }
            )

    write_json_report(
        "content-manifest",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        },
    )
    print(f"Built {len(entries)} generated content files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
