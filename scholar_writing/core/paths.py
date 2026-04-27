import os
from pathlib import Path


def find_repo_root(start=None):
    """Find the repository root by walking upward from start."""
    runtime_root = os.environ.get("SCHOLAR_WRITING_RUNTIME")
    if runtime_root:
        candidate = Path(runtime_root).resolve()
        if (candidate / "README.md").exists() and (candidate / "scholar_writing" / "resources").is_dir():
            return candidate
        raise FileNotFoundError(f"SCHOLAR_WRITING_RUNTIME is not a ScholarWriting runtime: {candidate}")

    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if (candidate / "README.md").exists() and (candidate / "scholar_writing" / "resources").is_dir():
            return candidate

    raise FileNotFoundError(f"Cannot find ScholarWriting repo root from {current}")


def framework_root(repo_root=None):
    """Return the framework resource directory."""
    root = Path(repo_root) if repo_root else find_repo_root()
    return root / "scholar_writing" / "resources"


def schema_path(data_type, repo_root=None):
    """Return the schema path for a data type."""
    return framework_root(repo_root) / "schemas" / f"{data_type}.schema.yaml"


def default_config_path(repo_root=None):
    """Return the framework default config path."""
    return framework_root(repo_root) / "config" / "default_config.yaml"


def reference_registry_path(repo_root=None):
    """Return the framework reference registry path."""
    return framework_root(repo_root) / "config" / "reference_registry.yaml"
