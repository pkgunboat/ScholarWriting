from pathlib import Path

import yaml

from scholar_writing.core.config import load_project_config
from scholar_writing.core.paths import find_repo_root
from scholar_writing.core.state import read_state
from scholar_writing.core.taskpack import build_taskpack
from scholar_writing.core.schema import validate_data


def flatten_paths(taskpack):
    paths = []
    for group in taskpack["reference_inputs"].values():
        paths.extend(item["path"] for item in group)
    return paths


def build_example_taskpack(example_name):
    repo_root = find_repo_root(Path(__file__))
    project_dir = repo_root / "examples" / example_name
    config = load_project_config(project_dir, repo_root)
    state = read_state(project_dir)
    return build_taskpack(project_dir, config, state)


def test_from_materials_taskpack_contains_architect_references():
    taskpack = build_example_taskpack("from-materials")
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_architect"
    assert "scholar_writing/resources/references/NSFC_GUIDE.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_from_outline_taskpack_contains_writer_references():
    taskpack = build_example_taskpack("from-outline")
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_writer"
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in paths
    assert "scholar_writing/resources/references/SENTENCE_PATTERNS_ZH.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_from_draft_taskpack_contains_reviewer_references():
    taskpack = build_example_taskpack("from-draft")
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_reviewers"
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in paths
    assert "scholar_writing/resources/references/DEAI_PATTERNS_ZH.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_taskpack_reference_inputs_validate_against_schema():
    repo_root = find_repo_root(Path(__file__))
    taskpack = build_example_taskpack("from-outline")

    assert validate_data("taskpack", taskpack, repo_root) == []
    for path in flatten_paths(taskpack):
        assert not Path(path).is_absolute()


def test_cli_taskpack_outputs_reference_inputs():
    repo_root = find_repo_root(Path(__file__))
    taskpack = build_example_taskpack("from-outline")
    serialized = yaml.safe_dump(taskpack, allow_unicode=True)

    assert "reference_inputs:" in serialized
    assert "STYLE_GUIDE_ZH.md" in serialized
