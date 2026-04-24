from pathlib import Path

import yaml

from .config import load_default_config
from .state import create_initial_state, write_state

SUPPORTED_INPUT_MODES = {"from_materials", "from_outline", "from_draft"}


def detect_input_mode(project_dir, config):
    """Detect the effective input mode for a project."""
    project = (config or {}).get("project", {})
    configured = project.get("input_mode", "auto")
    if configured in SUPPORTED_INPUT_MODES:
        return configured
    if configured != "auto":
        raise ValueError(f"Unsupported input_mode: {configured}")

    root = Path(project_dir)
    if any((root / "sections").glob("*.md")):
        return "from_draft"
    if (root / "planning" / "outline.md").exists():
        return "from_outline"
    if (root / "materials" / "manifest.yaml").exists() or (root / "materials").is_dir():
        return "from_materials"
    return "needs_user_input"


def init_project(project_dir, repo_root=None, project_type="nsfc", mode="auto", name=None):
    """Create a standard project skeleton with config.yaml and scores.yaml."""
    root = Path(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    for dirname in ["materials", "planning", "sections", "reviews", "revisions"]:
        (root / dirname).mkdir(exist_ok=True)

    config = load_default_config(repo_root)
    config.setdefault("project", {})
    config["project"]["type"] = project_type
    config["project"]["input_mode"] = mode
    if name:
        config["project"]["name"] = name

    config_path = root / "config.yaml"
    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    if not (root / "scores.yaml").exists():
        write_state(root, create_initial_state())

    return {
        "project_dir": str(root),
        "config_path": str(config_path),
        "scores_path": str(root / "scores.yaml"),
    }
