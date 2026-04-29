from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.io import write_json
from scripts.core.linkgraph import build_linkgraph, collect_outgoing_links
from scripts.core.page_catalog import collect_page_catalog
from scripts.core.paths import KNOWLEDGE_DIR
from scripts.core.registry import discover_workflows


def main(argv: list[str] | None = None) -> int:
    workflows = discover_workflows()
    content_dir = next(iter(workflows.values())).output_root.parent if workflows else None
    pages_by_link = collect_page_catalog(workflows, content_dir=content_dir) if content_dir else {}
    outgoing_links_by_link = collect_outgoing_links(workflows, pages_by_link, content_dir=content_dir) if content_dir else {}
    linkgraph = build_linkgraph(pages_by_link, outgoing_links_by_link)

    write_json(KNOWLEDGE_DIR / "pages.generated.json", pages_by_link)
    write_json(KNOWLEDGE_DIR / "linkgraph.generated.json", linkgraph)
    print(f"Built knowledge page catalog and linkgraph for {len(pages_by_link)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
