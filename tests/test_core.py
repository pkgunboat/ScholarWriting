from pathlib import Path

import yaml

from scholar_writing.core.config import load_default_config, load_project_config
from scholar_writing.core.paths import find_repo_root, framework_root, schema_path
from scholar_writing.core.project import detect_input_mode
from scholar_writing.core.schema import validate_data
from scholar_writing.core.state import create_initial_state, read_state, write_state
from scholar_writing.core.taskpack import build_taskpack
from scholar_writing.core.workflow import advance_state, next_action


def test_core_paths_resolve_repo_resources():
    repo_root = find_repo_root(Path(__file__))

    assert (repo_root / "README.md").exists()
    assert framework_root(repo_root) == repo_root / "scholar-writing"
    assert schema_path("config", repo_root).name == "config.schema.yaml"


def test_default_config_validates_against_schema():
    repo_root = find_repo_root(Path(__file__))
    config = load_default_config(repo_root)
    errors = validate_data("config", config, repo_root)

    assert config["project"]["input_mode"] == "auto"
    assert errors == []


def test_project_config_merges_over_default(tmp_path):
    repo_root = find_repo_root(Path(__file__))
    project_config = tmp_path / "config.yaml"
    project_config.write_text(
        """
project:
  name: 测试项目
  input_mode: from_outline
convergence:
  max_section_rounds: 2
""",
        encoding="utf-8",
    )

    config = load_project_config(tmp_path, repo_root)

    assert config["project"]["name"] == "测试项目"
    assert config["project"]["type"] == "nsfc"
    assert config["project"]["input_mode"] == "from_outline"
    assert config["convergence"]["max_section_rounds"] == 2


def test_detect_input_mode_auto_uses_project_files(tmp_path):
    config = {"project": {"input_mode": "auto"}}

    (tmp_path / "materials").mkdir()
    (tmp_path / "materials" / "manifest.yaml").write_text("materials: []\n", encoding="utf-8")
    assert detect_input_mode(tmp_path, config) == "from_materials"

    (tmp_path / "planning").mkdir()
    (tmp_path / "planning" / "outline.md").write_text("---\n{}\n---\n", encoding="utf-8")
    assert detect_input_mode(tmp_path, config) == "from_outline"

    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")
    assert detect_input_mode(tmp_path, config) == "from_draft"


def test_state_roundtrip(tmp_path):
    state = create_initial_state(["摘要", "立项依据"])
    write_state(tmp_path, state)

    loaded = read_state(tmp_path)

    assert loaded["phase"] == "initialized"
    assert set(loaded["sections"].keys()) == {"摘要", "立项依据"}


def test_next_action_for_supported_input_modes(tmp_path):
    config = {"project": {"input_mode": "auto"}}
    state = create_initial_state(["摘要"])

    (tmp_path / "materials").mkdir()
    (tmp_path / "materials" / "manifest.yaml").write_text("materials: []\n", encoding="utf-8")
    assert next_action(tmp_path, config, state)["action"] == "run_architect"

    (tmp_path / "planning").mkdir()
    (tmp_path / "planning" / "outline.md").write_text("---\n{}\n---\n", encoding="utf-8")
    assert next_action(tmp_path, config, state)["action"] == "run_writer"

    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")
    assert next_action(tmp_path, config, state)["action"] == "run_reviewers"


def test_next_action_runs_revision_unless_confirmation_required(tmp_path):
    config = {"project": {"input_mode": "from_draft"}}
    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")

    state = create_initial_state(["摘要"])
    state["phase"] = "section_revision"
    state["revision"] = {"requires_user_confirmation": False}
    assert next_action(tmp_path, config, state)["action"] == "run_revision"

    state["revision"]["requires_user_confirmation"] = True
    state["revision"]["confirmation_reason"] = "critical issue changes core claim"
    action = next_action(tmp_path, config, state)
    assert action["action"] == "ask_user"
    assert "critical issue" in action["reason"]


def test_advance_state_low_score_review_enters_revision(tmp_path):
    config = load_default_config(find_repo_root(Path(__file__)))
    state = create_initial_state(["摘要"])
    state["phase"] = "section_reviewing"
    review_result = {
        "section": "摘要",
        "round": 1,
        "scores": {"logic": 70, "de_ai": 72, "completeness": 74},
        "issues": [{"severity": "major", "message": "论证链不足"}],
    }

    updated = advance_state(state, config, event={"kind": "review_result", "data": review_result})

    assert updated["phase"] == "section_revision"
    assert updated["sections"]["摘要"]["current_score"] < 80
    assert updated["revision"]["requires_user_confirmation"] is False
    assert updated["next_action"]["action"] == "run_revision"


def test_advance_state_critical_review_requires_confirmation(tmp_path):
    config = load_default_config(find_repo_root(Path(__file__)))
    state = create_initial_state(["摘要"])
    state["phase"] = "section_reviewing"
    review_result = {
        "section": "摘要",
        "round": 1,
        "scores": {"logic": 40, "de_ai": 70, "completeness": 72},
        "issues": [{"severity": "critical", "message": "核心论点需要重写"}],
    }

    updated = advance_state(state, config, event={"kind": "review_result", "data": review_result})

    assert updated["phase"] == "section_revision"
    assert updated["revision"]["requires_user_confirmation"] is True
    assert updated["next_action"]["action"] == "ask_user"


def test_advance_state_high_score_review_completes_section(tmp_path):
    config = load_default_config(find_repo_root(Path(__file__)))
    state = create_initial_state(["摘要"])
    state["phase"] = "section_reviewing"
    review_result = {
        "section": "摘要",
        "round": 2,
        "scores": {"logic": 86, "de_ai": 82, "completeness": 88},
        "issues": [],
    }

    updated = advance_state(state, config, event={"kind": "review_result", "data": review_result})

    assert updated["sections"]["摘要"]["status"] == "approved"
    assert updated["phase"] == "complete"
    assert updated["next_action"]["action"] == "stop_complete"


def test_taskpack_validates_against_schema(tmp_path):
    repo_root = find_repo_root(Path(__file__))
    config = {"project": {"input_mode": "from_outline"}}
    state = create_initial_state(["摘要"])
    (tmp_path / "planning").mkdir()
    (tmp_path / "planning" / "outline.md").write_text("---\n{}\n---\n", encoding="utf-8")

    taskpack = build_taskpack(tmp_path, config, state)

    assert validate_data("taskpack", taskpack, repo_root) == []


def test_revision_log_fixture_validates_against_schema():
    repo_root = find_repo_root(Path(__file__))
    data = yaml.safe_load((repo_root / "tests" / "fixtures" / "revision-log.yaml").read_text(encoding="utf-8"))

    assert validate_data("revision_log", data, repo_root) == []


def test_review_result_fixtures_validate_against_schema():
    repo_root = find_repo_root(Path(__file__))
    for fixture_name in ["review-low.yaml", "review-pass.yaml"]:
        data = yaml.safe_load((repo_root / "tests" / "fixtures" / fixture_name).read_text(encoding="utf-8"))
        assert validate_data("review_result", data, repo_root) == []


def test_platform_neutral_prompts_exist_without_claude_agent_calls():
    repo_root = find_repo_root(Path(__file__))
    prompts_dir = repo_root / "scholar_writing" / "prompts"
    for name in ["architect.md", "writer.md", "reviewer.md", "revision.md"]:
        content = (prompts_dir / name).read_text(encoding="utf-8")
        assert "Agent(" not in content
        assert "task pack" in content or "task pack" in content.lower()
