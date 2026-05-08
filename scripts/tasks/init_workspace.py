from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.paths import resolve_workspace_path

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates" / "workspace"
DIRECTORY_SKELETON = (
    Path("incoming") / "new",
    Path("incoming") / "review",
    Path("sources") / "notes",
    Path("sources") / "docs",
)


def write_template(target: Path, template_name: str, *, force: bool) -> None:
    if target.exists() and not force:
        return
    shutil.copyfile(TEMPLATES_DIR / template_name, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    workspace_root = resolve_workspace_path(args.path)
    workspace_root.mkdir(parents=True, exist_ok=True)

    for rel_path in DIRECTORY_SKELETON:
        (workspace_root / rel_path).mkdir(parents=True, exist_ok=True)

    write_template(workspace_root / ".gitignore", ".gitignore", force=args.force)
    write_template(workspace_root / "README.md", "README.md", force=args.force)
    write_template(workspace_root / "Makefile", "Makefile", force=args.force)

    print(workspace_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
