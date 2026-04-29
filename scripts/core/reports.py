from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.core.io import write_text
from scripts.core.paths import BUILD_REPORTS_DIR


def report_path(name: str, reports_dir: Path = BUILD_REPORTS_DIR) -> Path:
    filename = name if name.endswith(".json") else f"{name}.json"
    return reports_dir / filename


def write_json_report(name: str, data: Any, reports_dir: Path = BUILD_REPORTS_DIR) -> Path:
    path = report_path(name, reports_dir)
    write_text(path, json.dumps(data, indent=2, ensure_ascii=True) + "\n")
    return path


def load_json_report(name: str, reports_dir: Path = BUILD_REPORTS_DIR) -> Any:
    return json.loads(report_path(name, reports_dir).read_text())
