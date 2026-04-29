from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.index_builder import collect_index_entries
from scripts.core.io import write_text
from scripts.core.paths import CONTENT_DIR, ROOT
from scripts.core.registry import discover_workflows
from scripts.core.sidebar_builder import build_nav_data, build_sidebar_data, render_nav_ts, render_sidebar_ts


def main(argv: list[str] | None = None) -> int:
    workflows = discover_workflows()
    entries = collect_index_entries(workflows, content_dir=CONTENT_DIR)

    write_text(ROOT / ".vitepress" / "sidebar.generated.ts", render_sidebar_ts(build_sidebar_data(entries)))
    write_text(ROOT / ".vitepress" / "nav.generated.ts", render_nav_ts(build_nav_data(entries)))
    print("Built generated sidebar and nav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
