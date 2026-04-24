from pathlib import Path

from .paths import find_repo_root, reference_registry_path
from .schema import load_yaml


def load_reference_registry(repo_root=None):
    """Load the framework reference registry."""
    return load_yaml(reference_registry_path(repo_root))


def _matches(value, allowed):
    return not allowed or value in allowed


def _matches_review_dimensions(review_dimensions, allowed):
    if not allowed:
        return True
    if not review_dimensions:
        return False
    return bool(set(review_dimensions) & set(allowed))


def _reference_input(ref_id, ref, reason=None):
    return {
        "id": ref_id,
        "path": ref["path"],
        "reason": reason or ref.get("purpose", ref_id),
    }


def _append_unique(groups, group_name, item):
    existing = {entry["id"] for values in groups.values() for entry in values}
    if item["id"] not in existing:
        groups[group_name].append(item)


def _validate_reference_paths(reference_inputs, repo_root):
    for group in reference_inputs.values():
        for item in group:
            path = Path(item["path"])
            if path.is_absolute():
                raise ValueError(f"Reference path must be relative: {item['path']}")
            if not (Path(repo_root) / path).exists():
                raise FileNotFoundError(f"Reference file does not exist: {item['path']}")


def select_references(
    *,
    project_type,
    action,
    agent_role,
    target_section=None,
    review_dimensions=None,
    language="zh",
    registry=None,
    repo_root=None,
):
    """Select reference inputs for a deterministic agent task pack."""
    root = Path(repo_root) if repo_root else find_repo_root()
    registry = registry or load_reference_registry(root)
    review_dimensions = review_dimensions or []
    groups = {
        "required": [],
        "section_specific": [],
        "optional": [],
    }

    for ref_id, ref in registry.get("references", {}).items():
        applies_to = ref.get("applies_to", {})
        if not _matches(project_type, applies_to.get("project_types")):
            continue
        if not _matches(language, applies_to.get("languages")):
            continue
        if not _matches(agent_role, applies_to.get("agent_roles")):
            continue
        if not _matches(action, applies_to.get("actions")):
            continue
        if action in {"run_reviewers", "run_revision"} and not _matches_review_dimensions(
            review_dimensions,
            applies_to.get("review_dimensions"),
        ):
            continue

        group_name = "optional" if ref.get("category") == "patterns" and action == "run_revision" else "required"
        _append_unique(groups, group_name, _reference_input(ref_id, ref))

    if action in {"run_writer", "run_reviewers", "run_revision"} and target_section:
        section_path = registry.get("section_patterns", {}).get(project_type, {}).get(target_section)
        if section_path:
            _append_unique(groups, "section_specific", {
                "id": f"pattern_{target_section}",
                "path": section_path,
                "reason": f"{target_section} 章节句式模板",
            })

    _validate_reference_paths(groups, root)
    return groups
