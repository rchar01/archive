from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

from scripts.core import paths
from scripts.core.sections import normalize_section_path
from scripts.core.slug import slugify


def resolve_output_slug(title: str, slug: str | None = None) -> str:
    cleaned = str(slug or "").strip()
    return cleaned or slugify(title)


@dataclass(frozen=True)
class WorkflowDefinition:
    kind: str
    label: str
    source_root: Path
    output_root: Path
    default_section: str
    required_sections: tuple[str, ...]
    knowledge_panel: bool | None
    backlinks: bool | None
    related: bool | None
    workflow_dir: Path

    @property
    def config_path(self) -> Path:
        return self.workflow_dir / "workflow.yml"

    @property
    def template_path(self) -> Path:
        return self.workflow_dir / "template.md"

    def module_path(self, name: str) -> Path:
        return self.workflow_dir / f"{name}.py"

    def normalize_section(self, section: str | None = None) -> str:
        return normalize_section_path(section, default_section=self.default_section)

    def source_path_for(self, title: str, section: str | None = None) -> Path:
        normalized_section = self.normalize_section(section)
        return self.source_root / normalized_section / f"{slugify(title)}.md"

    def output_path_for(self, title: str, section: str | None = None, slug: str | None = None) -> Path:
        normalized_section = self.normalize_section(section)
        return self.output_root / normalized_section / f"{resolve_output_slug(title, slug)}.md"

    def load_module(self, name: str) -> ModuleType:
        path = self.module_path(name)
        if not path.exists():
            raise FileNotFoundError(path)
        module_name = f"scripts.workflows.{self.kind}.{name}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load workflow module: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def load_workflow_config(path: Path) -> WorkflowDefinition:
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Workflow config must be a mapping: {path}")

    kind = str(data.get("kind") or "").strip()
    if not kind:
        raise ValueError(f"Workflow config missing kind: {path}")

    label = str(data.get("label") or kind.title()).strip()
    source_root = paths.resolve_workspace_path(str(data.get("source_root") or ""))
    output_root = paths.resolve_workflow_output_root(str(data.get("output_root") or ""))
    default_section = str(data.get("default_section") or "general").strip() or "general"
    required_sections = tuple(str(section).strip() for section in data.get("required_sections") or [] if str(section).strip())

    knowledge_panel = data.get("knowledge_panel")
    if knowledge_panel is not None and not isinstance(knowledge_panel, bool):
        raise ValueError(f"Workflow config field 'knowledge_panel' must be a boolean: {path}")

    backlinks = data.get("backlinks")
    if backlinks is not None and not isinstance(backlinks, bool):
        raise ValueError(f"Workflow config field 'backlinks' must be a boolean: {path}")

    related = data.get("related")
    if related is not None and not isinstance(related, bool):
        raise ValueError(f"Workflow config field 'related' must be a boolean: {path}")

    if not str(data.get("source_root") or "").strip():
        raise ValueError(f"Workflow config missing source_root: {path}")
    if not str(data.get("output_root") or "").strip():
        raise ValueError(f"Workflow config missing output_root: {path}")

    return WorkflowDefinition(
        kind=kind,
        label=label,
        source_root=source_root,
        output_root=output_root,
        default_section=default_section,
        required_sections=required_sections,
        knowledge_panel=knowledge_panel,
        backlinks=backlinks,
        related=related,
        workflow_dir=path.parent,
    )


def discover_workflows(workflows_dir: Path | None = None) -> dict[str, WorkflowDefinition]:
    workflows_root = workflows_dir or paths.workflows_dir()
    workflows: dict[str, WorkflowDefinition] = {}
    for config_path in sorted(workflows_root.glob("*/workflow.yml")):
        workflow = load_workflow_config(config_path)
        workflows[workflow.kind] = workflow
    return workflows


def get_workflow(kind: str, workflows_dir: Path | None = None) -> WorkflowDefinition:
    workflows = discover_workflows(workflows_dir)
    if kind not in workflows:
        raise KeyError(f"Unknown workflow kind: {kind}")
    return workflows[kind]


def workflow_kinds(workflows_dir: Path | None = None) -> list[str]:
    return sorted(discover_workflows(workflows_dir))
