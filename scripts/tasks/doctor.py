from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.paths import build_dir, content_dir, incoming_dir, sources_dir, workflows_dir
from scripts.core.registry import discover_workflows


def main(argv: list[str] | None = None) -> int:
    for path in (incoming_dir(), sources_dir(), content_dir(), build_dir(), workflows_dir()):
        if not path.exists():
            raise SystemExit(f"Missing required path: {path}")

    workflows = discover_workflows()
    if not workflows:
        raise SystemExit("No workflows discovered")

    for workflow in workflows.values():
        if not workflow.template_path.exists():
            raise SystemExit(f"Missing workflow template: {workflow.template_path}")
        for module_name in ("adapter", "renderer", "validator"):
            if not workflow.module_path(module_name).exists():
                raise SystemExit(f"Missing workflow module: {workflow.module_path(module_name)}")

    print(f"Doctor OK: {len(workflows)} workflows discovered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
