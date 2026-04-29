from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())
