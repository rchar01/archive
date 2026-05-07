from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.frontmatter import read_markdown
from scripts.core.markdown import markdown_files
from scripts.core.paths import relative_to_workspace
from scripts.core.registry import discover_workflows
from scripts.core.reports import write_json_report
from scripts.core.validation import (
    ValidationError,
    body_start_line,
    check_body_lints,
    check_duplicate_ids,
    check_duplicate_output_paths,
    require_field,
    require_optional_slug,
)


def main(argv: list[str] | None = None) -> int:
    workflows = discover_workflows()
    entries: list[dict[str, str]] = []
    ids: list[str] = []
    output_paths: list[str] = []

    for workflow in workflows.values():
        validator = workflow.load_module("validator")
        for path in markdown_files(workflow.source_root):
            raw_text = path.read_text()
            document = read_markdown(path)
            try:
                validator.validate(document, required_sections=workflow.required_sections)
                check_body_lints(document.body, start_line=body_start_line(raw_text))
                title = str(require_field(document.frontmatter, "title")).strip()
                section = workflow.normalize_section(str(require_field(document.frontmatter, "section")).strip())
                slug = require_optional_slug(document.frontmatter, "slug")
                ids.append(str(require_field(document.frontmatter, "id")).strip())
                output_paths.append(workflow.output_path_for(title, section, slug=slug).as_posix())
                entries.append({"path": relative_to_workspace(path), "kind": workflow.kind})
            except ValidationError as exc:
                raise ValidationError(f"{relative_to_workspace(path)}: {exc}") from exc

    check_duplicate_ids(ids)
    check_duplicate_output_paths(output_paths)
    write_json_report("validation", {"entries": entries, "count": len(entries)})
    print(f"Validated {len(entries)} source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
