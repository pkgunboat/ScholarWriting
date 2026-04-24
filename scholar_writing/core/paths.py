from pathlib import Path


def find_repo_root(start=None):
    """Find the repository root by walking upward from start."""
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if (candidate / "README.md").exists() and (candidate / "scholar-writing").is_dir():
            return candidate

    raise FileNotFoundError(f"Cannot find ScholarWriting repo root from {current}")


def framework_root(repo_root=None):
    """Return the legacy framework resource directory."""
    root = Path(repo_root) if repo_root else find_repo_root()
    return root / "scholar-writing"


def schema_path(data_type, repo_root=None):
    """Return the schema path for a data type."""
    return framework_root(repo_root) / "schemas" / f"{data_type}.schema.yaml"


def default_config_path(repo_root=None):
    """Return the framework default config path."""
    return framework_root(repo_root) / "config" / "default_config.yaml"
