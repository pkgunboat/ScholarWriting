from pathlib import Path

from .references import select_references
from .workflow import next_action


def build_taskpack(project_dir, config, state):
    """Build a minimal task pack from the current next action."""
    project_dir = Path(project_dir)
    action = next_action(project_dir, config, state)
    kind = action["action"]
    base = {
        "task_id": f"{kind}-{project_dir.name}",
        "action": kind,
        "project_dir": str(project_dir),
        "input_mode": action.get("input_mode"),
        "reason": action.get("reason"),
    }

    if kind == "run_architect":
        base.update({
            "agent_role": "architect",
            "inputs": {
                "manifest_path": "materials/manifest.yaml",
                "config_path": "config.yaml",
            },
            "outputs": {
                "outline_path": "planning/outline.md",
                "claim_registry_path": "planning/claim_registry.md",
                "dependency_graph_path": "planning/dependency_graph.yaml",
            },
        })
    elif kind == "run_writer":
        base.update({
            "agent_role": "writer",
            "inputs": {
                "outline_path": "planning/outline.md",
                "claim_registry_path": "planning/claim_registry.md",
            },
            "outputs": {
                "sections_dir": "sections/",
            },
        })
    elif kind == "run_reviewers":
        base.update({
            "agent_role": "reviewer",
            "inputs": {
                "sections_dir": "sections/",
                "scores_path": "scores.yaml",
            },
            "review": {
                "dimensions": ["logic", "de_ai", "completeness", "format"],
            },
            "outputs": {
                "reviews_dir": "reviews/",
            },
        })
    elif kind == "run_revision":
        base.update({
            "agent_role": "revision",
            "inputs": {
                "reviews_dir": "reviews/",
                "scores_path": "scores.yaml",
            },
            "outputs": {
                "sections_dir": "sections/",
                "revisions_dir": "revisions/",
            },
            "requires_user_confirmation_when": [
                "critical_issue",
                "core_claim_change",
                "major_scope_change",
                "cross_section_impact",
            ],
        })
    else:
        base.update({
            "agent_role": "main",
            "inputs": {},
            "outputs": {},
        })

    base["reference_inputs"] = select_references(
        project_type=config.get("project", {}).get("type", "nsfc"),
        action=kind,
        agent_role=base["agent_role"],
        target_section=base.get("section", {}).get("id"),
        review_dimensions=base.get("review", {}).get("dimensions"),
        language=config.get("project", {}).get("language", "zh"),
    )

    return base
