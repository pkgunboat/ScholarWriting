from copy import deepcopy
from pathlib import Path

from .paths import default_config_path
from .schema import load_yaml, validate_data


def deep_merge(base, override):
    """Merge override into base recursively without mutating inputs."""
    result = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def load_default_config(repo_root=None):
    """Load the framework default config."""
    return load_yaml(default_config_path(repo_root))


def load_project_config(project_dir, repo_root=None):
    """Load project config.yaml merged over the default config."""
    default = load_default_config(repo_root)
    project_path = Path(project_dir) / "config.yaml"
    if not project_path.exists():
        return default
    return deep_merge(default, load_yaml(project_path))


def validate_config(config, repo_root=None):
    """Validate a config dict against the config schema."""
    return validate_data("config", config, repo_root)
