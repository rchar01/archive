from __future__ import annotations

import os
import re
from os import path as os_path
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parents[2]
ROOT = TOOL_ROOT


def _resolve_workspace_root() -> Path:
    raw_value = str(os.environ.get("WORKSPACE") or "").strip()
    if not raw_value:
        return TOOL_ROOT

    workspace = Path(raw_value).expanduser()
    if not workspace.is_absolute():
        workspace = Path.cwd() / workspace
    return workspace.resolve()


def _normalize_instance_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or "default"


def _resolve_archive_instance() -> str:
    raw_value = str(os.environ.get("ARCHIVE_INSTANCE") or "").strip()
    if raw_value:
        return _normalize_instance_name(raw_value)

    workspace = _resolve_workspace_root()
    if workspace == TOOL_ROOT:
        return "default"
    return _normalize_instance_name(workspace.name)


def _use_legacy_generated_layout() -> bool:
    return _resolve_archive_instance() == "default" and _resolve_workspace_root() == TOOL_ROOT


WORKSPACE_ROOT = _resolve_workspace_root()
ARCHIVE_INSTANCE = _resolve_archive_instance()
INSTANCE_ROOT = TOOL_ROOT / ".instances" / ARCHIVE_INSTANCE
USE_LEGACY_GENERATED_LAYOUT = _use_legacy_generated_layout()
VITEPRESS_DIR = TOOL_ROOT / ".vitepress"
GENERATED_VITEPRESS_DIR = VITEPRESS_DIR if USE_LEGACY_GENERATED_LAYOUT else INSTANCE_ROOT / "generated"
KNOWLEDGE_DIR = GENERATED_VITEPRESS_DIR / "knowledge"
INCOMING_DIR = WORKSPACE_ROOT / "incoming"
INCOMING_NEW_DIR = INCOMING_DIR / "new"
INCOMING_REVIEW_DIR = INCOMING_DIR / "review"
SOURCES_DIR = WORKSPACE_ROOT / "sources"
NOTES_DIR = SOURCES_DIR / "notes"
DOCS_SOURCES_DIR = SOURCES_DIR / "docs"
CONTENT_DIR = TOOL_ROOT / "content" if USE_LEGACY_GENERATED_LAYOUT else INSTANCE_ROOT / "content"
SITE_DIR = TOOL_ROOT / "site" if USE_LEGACY_GENERATED_LAYOUT else INSTANCE_ROOT / "site"
BUILD_DIR = TOOL_ROOT / "build" if USE_LEGACY_GENERATED_LAYOUT else INSTANCE_ROOT / "build"
BUILD_REPORTS_DIR = BUILD_DIR / "reports"
BUILD_CACHE_DIR = BUILD_DIR / "cache"
SCRIPTS_DIR = TOOL_ROOT / "scripts"
WORKFLOWS_DIR = SCRIPTS_DIR / "workflows"
TASKS_DIR = SCRIPTS_DIR / "tasks"
RUNTIME_DIR = SCRIPTS_DIR / "runtime"


def tool_root() -> Path:
    return TOOL_ROOT


def workspace_root() -> Path:
    return _resolve_workspace_root()


def archive_instance() -> str:
    return _resolve_archive_instance()


def instance_root() -> Path:
    return tool_root() / ".instances" / archive_instance()


def use_legacy_generated_layout() -> bool:
    return _use_legacy_generated_layout()


def repo_root() -> Path:
    return tool_root()


def resolve_tool_path(*parts: str | Path) -> Path:
    return tool_root().joinpath(*parts)


def resolve_workspace_path(*parts: str | Path) -> Path:
    return workspace_root().joinpath(*parts)


def vitepress_dir() -> Path:
    return VITEPRESS_DIR


def generated_vitepress_dir() -> Path:
    return GENERATED_VITEPRESS_DIR


def knowledge_dir() -> Path:
    return KNOWLEDGE_DIR


def incoming_dir() -> Path:
    return resolve_workspace_path("incoming")


def incoming_new_dir() -> Path:
    return incoming_dir() / "new"


def incoming_review_dir() -> Path:
    return incoming_dir() / "review"


def sources_dir() -> Path:
    return resolve_workspace_path("sources")


def notes_dir() -> Path:
    return sources_dir() / "notes"


def docs_sources_dir() -> Path:
    return sources_dir() / "docs"


def content_dir() -> Path:
    return CONTENT_DIR


def site_dir() -> Path:
    return SITE_DIR


def build_dir() -> Path:
    return BUILD_DIR


def generated_vitepress_file(name: str) -> Path:
    return generated_vitepress_dir() / name


def resolve_workflow_output_root(raw_value: str) -> Path:
    cleaned = raw_value.strip()
    if cleaned == "content":
        return content_dir()
    if cleaned.startswith("content/"):
        relative = cleaned.split("/", 1)[1]
        return content_dir() / relative
    return resolve_tool_path(cleaned)


def build_reports_dir() -> Path:
    return BUILD_REPORTS_DIR


def build_cache_dir() -> Path:
    return BUILD_CACHE_DIR


def workflows_dir() -> Path:
    return WORKFLOWS_DIR


def tasks_dir() -> Path:
    return TASKS_DIR


def runtime_dir() -> Path:
    return RUNTIME_DIR


def trim(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def slugify(value: str) -> str:
    from scripts.core.slug import slugify as core_slugify

    return core_slugify(value)


def safe_join(base: Path, *parts: str) -> Path:
    base_path = base.resolve()
    candidate = base.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base_path)
    except ValueError as exc:
        raise ValueError(f"Resolved path escapes base directory: {candidate}") from exc
    return candidate


def ensure_parent_dir(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def relative_to_tool(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(tool_root()).as_posix()
    except ValueError:
        return resolved.as_posix()


def relative_to_workspace(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace_root()).as_posix()
    except ValueError:
        return resolved.as_posix()


def relative_to_repo(path: Path) -> str:
    return relative_to_tool(path)


def relative_link(from_path: Path, to_path: Path) -> str:
    return os_path.relpath(to_path, start=from_path.parent).replace("\\", "/")
