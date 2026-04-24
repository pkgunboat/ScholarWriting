from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from .paths import schema_path


def load_schema(data_type, repo_root=None):
    """Load a YAML JSON Schema by data type."""
    path = schema_path(data_type, repo_root)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_data(data_type, data, repo_root=None):
    """Validate data and return a compact list of error strings."""
    schema = load_schema(data_type, repo_root)
    validator = Draft7Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path)
        if path:
            errors.append(f"{path}: {error.message}")
        else:
            errors.append(error.message)
    return sorted(errors)


def load_yaml(path):
    """Load a YAML file as a dict."""
    with open(Path(path), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}
