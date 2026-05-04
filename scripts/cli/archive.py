#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.frontmatter import MarkdownDocument, parse_frontmatter, render_markdown
from scripts.core.io import write_text
from scripts.core.slug import slugify


ARCHIVE_ROOT = Path(__file__).resolve().parents[2]
IN_CONTAINER = ARCHIVE_ROOT / "scripts" / "runtime" / "in-container"
WORKSPACE_MARKERS = (
    Path("incoming") / "new",
    Path("incoming") / "review",
    Path("sources") / "notes",
    Path("sources") / "docs",
)


def optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def parse_csv(value: str | None) -> list[str]:
    cleaned = optional_string(value)
    if cleaned is None:
        return []
    values: list[str] = []
    for item in cleaned.split(","):
        candidate = item.strip()
        if candidate and candidate not in values:
            values.append(candidate)
    return values


def normalize_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        candidate = optional_string(str(value))
        if candidate is not None and candidate not in cleaned:
            cleaned.append(candidate)
    return cleaned


def is_workspace_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in WORKSPACE_MARKERS)


def discover_workspace(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if is_workspace_root(candidate):
            return candidate.resolve()
    return None


def resolve_workspace(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    workspace = discover_workspace(Path.cwd().resolve())
    if workspace is not None:
        return workspace
    raise SystemExit("Could not infer workspace from current directory; pass --workspace /path/to/workspace")


def relative_to(base: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ARCHIVE_ROOT, env=env, check=True)


def run_make(target: str, *, workspace: Path) -> None:
    env = {**os.environ, "WORKSPACE": str(workspace)}
    run(["make", target], env=env)


def run_in_container(command: list[str], *, workspace: Path) -> None:
    env = {**os.environ, "WORKSPACE": str(workspace)}
    run([str(IN_CONTAINER), *command], env=env)


def humanize_stem(stem: str) -> str:
    words = [part for part in stem.replace("_", "-").split("-") if part]
    return " ".join(word.capitalize() for word in words) or "Imported Note"


def read_raw_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text()
    try:
        return parse_frontmatter(text)
    except Exception:
        # External raw imports may have broken frontmatter; keep the full file as body.
        return {}, text


def write_import_target(document: MarkdownDocument, *, workspace: Path, title: str, force: bool) -> Path:
    target = workspace / "incoming" / "new" / f"{slugify(title, fallback='entry')}.md"
    if target.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file: {relative_to(workspace, target)}")
    write_text(target, render_markdown(document))
    return target


def add_common_frontmatter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--slug")
    parser.add_argument("--nav-title")
    parser.add_argument("--summary")
    parser.add_argument("--priority")
    parser.add_argument("--tags")
    parser.add_argument("--related-manual", action="append", default=[])
    parser.add_argument("--hide-knowledge-panel", action="store_true", default=None)
    parser.add_argument("--hide-backlinks", action="store_true", default=None)
    parser.add_argument("--hide-related", action="store_true", default=None)


def build_import_frontmatter(args: argparse.Namespace, raw_frontmatter: dict[str, Any], *, title: str, kind: str) -> dict[str, Any]:
    processing = optional_string(args.processing) or optional_string(raw_frontmatter.get("processing")) or "review"
    if processing not in {"auto", "review"}:
        raise SystemExit("processing must be 'auto' or 'review'")

    frontmatter: dict[str, Any] = {
        "title": title,
        "kind": kind,
        "tags": parse_csv(args.tags) or normalize_list(raw_frontmatter.get("tags")),
        "processing": processing,
    }

    section = optional_string(args.section) or optional_string(raw_frontmatter.get("section"))
    if section is not None:
        frontmatter["section"] = section

    for name, source in (
        ("slug", args.slug),
        ("nav_title", args.nav_title),
        ("summary", args.summary),
        ("priority", args.priority),
    ):
        value = optional_string(source) or optional_string(raw_frontmatter.get(name))
        if value is not None:
            frontmatter[name] = value

    related_manual = []
    for value in args.related_manual:
        related_manual.extend(parse_csv(value))
    if not related_manual:
        related_manual = normalize_list(raw_frontmatter.get("related_manual"))
    if related_manual:
        frontmatter["related_manual"] = related_manual

    for name in ("hide_knowledge_panel", "hide_backlinks", "hide_related"):
        flag_value = getattr(args, name)
        if flag_value is True:
            frontmatter[name] = True
            continue
        raw_value = raw_frontmatter.get(name)
        if isinstance(raw_value, bool):
            frontmatter[name] = raw_value

    return frontmatter


def command_init_workspace(args: argparse.Namespace) -> int:
    command = ["python3", "scripts/tasks/init_workspace.py"]
    if args.force:
        command.append("--force")
    command.append(str(Path(args.path).expanduser()))
    run(command)
    return 0


def command_new(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(args.workspace)
    command = ["python3", "scripts/tasks/new_entry.py", "--kind", args.kind, "--title", args.title]
    if args.section:
        command.extend(["--section", args.section])
    if args.slug:
        command.extend(["--slug", args.slug])
    if args.nav_title:
        command.extend(["--nav-title", args.nav_title])
    if args.summary:
        command.extend(["--summary", args.summary])
    if args.priority:
        command.extend(["--priority", args.priority])
    if args.tags:
        command.extend(["--tags", args.tags])
    for value in args.related_manual:
        command.extend(["--related-manual", value])
    for flag, enabled in (
        ("--hide-knowledge-panel", args.hide_knowledge_panel),
        ("--hide-backlinks", args.hide_backlinks),
        ("--hide-related", args.hide_related),
    ):
        if enabled:
            command.append(flag)
    if args.force:
        command.append("--force")
    run_in_container(command, workspace=workspace)
    return 0


def command_import(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(args.workspace)
    source_path = Path(args.source).expanduser().resolve()
    if not source_path.is_file():
        raise SystemExit(f"Raw source file not found: {source_path}")

    raw_frontmatter, body = read_raw_markdown(source_path)
    title = optional_string(args.title) or optional_string(raw_frontmatter.get("title")) or humanize_stem(source_path.stem)
    kind = optional_string(args.kind) or optional_string(raw_frontmatter.get("kind"))
    if kind not in {"note", "doc"}:
        raise SystemExit("import requires kind 'note' or 'doc'; pass --kind when the raw file does not provide it")

    document = MarkdownDocument(
        frontmatter=build_import_frontmatter(args, raw_frontmatter, title=title, kind=kind),
        body=body.rstrip() + "\n" if body.strip() else "",
    )
    target = write_import_target(document, workspace=workspace, title=title, force=args.force)
    print(relative_to(workspace, target))

    if args.process:
        run_in_container(["python3", "scripts/tasks/process_incoming.py", "incoming/new"], workspace=workspace)
    return 0


def command_process(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(args.workspace)
    command = ["python3", "scripts/tasks/process_incoming.py", "incoming/new"]
    if args.force:
        command.append("--force")
    run_in_container(command, workspace=workspace)
    return 0


def command_accept(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(args.workspace)
    command = ["python3", "scripts/tasks/accept_review.py", args.file]
    if args.force:
        command.append("--force")
    run_in_container(command, workspace=workspace)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    run_make("validate", workspace=resolve_workspace(args.workspace))
    return 0


def command_build_content(args: argparse.Namespace) -> int:
    run_make("build-content", workspace=resolve_workspace(args.workspace))
    return 0


def command_build(args: argparse.Namespace) -> int:
    run_make("build", workspace=resolve_workspace(args.workspace))
    return 0


def command_check(args: argparse.Namespace) -> int:
    run_make("check", workspace=resolve_workspace(args.workspace))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archive", description="Archive authoring CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace", help="Bootstrap a private workspace")
    init_workspace.add_argument("path")
    init_workspace.add_argument("--force", action="store_true")
    init_workspace.set_defaults(func=command_init_workspace)

    new = subparsers.add_parser("new", help="Create a canonical source entry")
    new.add_argument("kind", choices=["note", "doc"])
    new.add_argument("--workspace")
    new.add_argument("--title", required=True)
    new.add_argument("--section")
    new.add_argument("--force", action="store_true")
    add_common_frontmatter_args(new)
    new.set_defaults(func=command_new)

    import_cmd = subparsers.add_parser("import", help="Stage a raw Markdown file into Archive intake")
    import_cmd.add_argument("source")
    import_cmd.add_argument("--workspace")
    import_cmd.add_argument("--kind", choices=["note", "doc"])
    import_cmd.add_argument("--title")
    import_cmd.add_argument("--section")
    import_cmd.add_argument("--processing", choices=["auto", "review"], default="review")
    import_cmd.add_argument("--process", action="store_true")
    import_cmd.add_argument("--force", action="store_true")
    add_common_frontmatter_args(import_cmd)
    import_cmd.set_defaults(func=command_import)

    process_cmd = subparsers.add_parser("process", help="Normalize queued files from incoming/new")
    process_cmd.add_argument("--workspace")
    process_cmd.add_argument("--force", action="store_true")
    process_cmd.set_defaults(func=command_process)

    accept = subparsers.add_parser("accept", help="Accept a reviewed draft into sources")
    accept.add_argument("file")
    accept.add_argument("--workspace")
    accept.add_argument("--force", action="store_true")
    accept.set_defaults(func=command_accept)

    validate = subparsers.add_parser("validate", help="Validate canonical sources")
    validate.add_argument("--workspace")
    validate.set_defaults(func=command_validate)

    build_content = subparsers.add_parser("build-content", help="Build generated content only")
    build_content.add_argument("--workspace")
    build_content.set_defaults(func=command_build_content)

    build = subparsers.add_parser("build", help="Build generated content and the static site")
    build.add_argument("--workspace")
    build.set_defaults(func=command_build)

    check = subparsers.add_parser("check", help="Run full verification")
    check.add_argument("--workspace")
    check.set_defaults(func=command_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
