from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_codex_repo_skill_exists_with_required_metadata():
    skill_path = REPO_ROOT / ".agents" / "skills" / "scholar-writing" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "name: scholar-writing" in content
    assert "description:" in content
    assert "uv run scholar-writing next" in content
    assert "scores.yaml" in content
    assert "reference_inputs" in content
    assert "quality rules" in content
    assert "Developer Debugging" in content
    assert ".codex/agents" in content
    assert "examples/from-draft" in content


def test_codex_custom_agents_exist_with_required_fields():
    agents_dir = REPO_ROOT / ".codex" / "agents"
    expected = {
        "scholar-architect.toml",
        "scholar-writer.toml",
        "scholar-reviewer.toml",
        "scholar-revision.toml",
    }

    assert {path.name for path in agents_dir.glob("*.toml")} == expected

    for file_name in expected:
        content = (agents_dir / file_name).read_text(encoding="utf-8")
        assert "name =" in content
        assert "description =" in content
        assert "developer_instructions =" in content
        assert "reference_inputs" in content


def test_developer_debugging_docs_cover_repo_local_workflow():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    codex_doc = (REPO_ROOT / "docs" / "codex-getting-started.md").read_text(encoding="utf-8")

    assert "源码仓库内调试" in readme
    assert "repo-local skill" in readme
    assert "临时 Codex Home" in codex_doc
    assert "CODEX_HOME=" in codex_doc


def test_platform_prompts_require_reference_inputs():
    prompts_dir = REPO_ROOT / "scholar_writing" / "prompts"
    for file_name in ["architect.md", "writer.md", "reviewer.md", "revision.md"]:
        content = (prompts_dir / file_name).read_text(encoding="utf-8")
        assert "reference_inputs" in content
        assert "规则" in content
