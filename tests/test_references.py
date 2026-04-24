from pathlib import Path

import pytest

from scholar_writing.core.paths import find_repo_root
from scholar_writing.core.references import load_reference_registry, select_references
from scholar_writing.core.schema import validate_data


def paths_for(reference_inputs):
    paths = []
    for group in reference_inputs.values():
        paths.extend(item["path"] for item in group)
    return paths


def test_reference_registry_validates_and_paths_exist():
    repo_root = find_repo_root(Path(__file__))
    registry = load_reference_registry(repo_root)

    assert validate_data("reference_registry", registry, repo_root) == []
    for item in registry["references"].values():
        path = Path(item["path"])
        assert not path.is_absolute()
        assert (repo_root / path).exists()
    for section_path in registry["section_patterns"]["nsfc"].values():
        path = Path(section_path)
        assert not path.is_absolute()
        assert (repo_root / path).exists()


def test_select_references_for_nsfc_architect():
    selected = select_references(
        project_type="nsfc",
        action="run_architect",
        agent_role="architect",
    )
    paths = paths_for(selected)

    assert "scholar-writing/references/NSFC_GUIDE.md" in paths
    assert "scholar-writing/references/NSFC_STRUCTURE_ZH.md" in paths
    assert all(not Path(path).is_absolute() for path in paths)


def test_select_references_for_nsfc_writer_section():
    selected = select_references(
        project_type="nsfc",
        action="run_writer",
        agent_role="writer",
        target_section="02_立项依据",
    )
    paths = paths_for(selected)

    assert "scholar-writing/references/STYLE_GUIDE_ZH.md" in paths
    assert "scholar-writing/references/SENTENCE_PATTERNS_ZH.md" in paths
    assert "scholar-writing/references/patterns/00_通用.md" in paths
    assert "scholar-writing/references/patterns/02_立项依据.md" in paths
    assert "scholar-writing/references/NSFC_STRUCTURE_ZH.md" in paths


def test_select_references_for_deai_review():
    selected = select_references(
        project_type="nsfc",
        action="run_reviewers",
        agent_role="reviewer",
        review_dimensions=["de_ai"],
    )
    paths = paths_for(selected)

    assert "scholar-writing/references/DEAI_PATTERNS_ZH.md" in paths
    assert "scholar-writing/references/STYLE_GUIDE_ZH.md" in paths


def test_missing_reference_file_raises_clear_error(tmp_path):
    registry = {
        "version": 1,
        "references": {
            "missing": {
                "path": "scholar-writing/references/MISSING.md",
                "purpose": "missing test",
                "applies_to": {
                    "project_types": ["nsfc"],
                    "agent_roles": ["writer"],
                    "actions": ["run_writer"],
                },
            }
        },
        "section_patterns": {},
    }

    with pytest.raises(FileNotFoundError, match="Reference file does not exist"):
        select_references(
            project_type="nsfc",
            action="run_writer",
            agent_role="writer",
            registry=registry,
            repo_root=tmp_path,
        )
