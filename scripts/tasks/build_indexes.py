from __future__ import annotations

import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.features import knowledge_graph_enabled
from scripts.core.index_builder import build_index_pages, collect_index_entries
from scripts.core.io import write_text
from scripts.core.paths import CONTENT_DIR
from scripts.core.registry import discover_workflows


def main(argv: list[str] | None = None) -> int:
    workflows = discover_workflows()
    entries = collect_index_entries(workflows, content_dir=CONTENT_DIR)
    graph_enabled = knowledge_graph_enabled()
    if not graph_enabled:
        shutil.rmtree(CONTENT_DIR / "graph", ignore_errors=True)

    workflow_pairs = [(workflow.output_root.relative_to(CONTENT_DIR).as_posix(), workflow.label) for workflow in workflows.values()]
    for rel_path, content in build_index_pages(
        entries,
        workflows=workflow_pairs,
        workflow_definitions=workflows,
        knowledge_graph_enabled=graph_enabled,
    ).items():
        write_text(CONTENT_DIR / rel_path, content)

    print("Built generated indexes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
