from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.features import knowledge_graph_enabled
from scripts.core.index_builder import collect_index_entries
from scripts.core.io import write_json, write_text
from scripts.core.paths import CONTENT_DIR, GENERATED_VITEPRESS_DIR
from scripts.core.registry import discover_workflows
from scripts.core.sidebar_builder import build_nav_data, build_sidebar_data, render_nav_ts, render_sidebar_ts


def main(argv: list[str] | None = None) -> int:
    workflows = discover_workflows()
    entries = collect_index_entries(workflows, content_dir=CONTENT_DIR)
    sidebar = build_sidebar_data(entries, workflow_definitions=workflows)
    nav = build_nav_data(entries, knowledge_graph_enabled=knowledge_graph_enabled())

    write_json(GENERATED_VITEPRESS_DIR / "sidebar.generated.json", sidebar)
    write_json(GENERATED_VITEPRESS_DIR / "nav.generated.json", nav)
    write_text(GENERATED_VITEPRESS_DIR / "sidebar.generated.ts", render_sidebar_ts(sidebar))
    write_text(GENERATED_VITEPRESS_DIR / "nav.generated.ts", render_nav_ts(nav))
    print("Built generated sidebar and nav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
