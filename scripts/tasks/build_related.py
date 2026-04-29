from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.io import read_json, write_json
from scripts.core.paths import KNOWLEDGE_DIR
from scripts.core.related import build_related_index


def main(argv: list[str] | None = None) -> int:
    pages_by_link = read_json(KNOWLEDGE_DIR / "pages.generated.json")
    linkgraph = read_json(KNOWLEDGE_DIR / "linkgraph.generated.json")
    related_index = build_related_index(pages_by_link, linkgraph)

    write_json(KNOWLEDGE_DIR / "related.generated.json", related_index)
    print(f"Built related suggestions for {len(related_index)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
