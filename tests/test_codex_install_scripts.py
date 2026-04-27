import os
import subprocess
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_script(script_name, codex_home, *extra_args):
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    return subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / script_name), "--no-sync", *extra_args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_codex_install_and_uninstall_roundtrip(tmp_path):
    codex_home = tmp_path / "codex-home"

    install = run_script("install-codex.sh", codex_home)

    assert install.returncode == 0, install.stderr
    skill_dir = codex_home / "skills" / "scholar-writing"
    runtime_dir = skill_dir / "runtime"
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "bin" / "scholar-writing").exists()
    assert os.access(skill_dir / "bin" / "scholar-writing", os.X_OK)
    assert (runtime_dir / "pyproject.toml").exists()
    assert (runtime_dir / "scholar_writing" / "resources" / "references" / "STYLE_GUIDE_ZH.md").exists()
    assert (runtime_dir / "scholar_writing" / "cli.py").exists()
    assert (runtime_dir / "scholar_writing" / "prompts" / "writer.md").exists()
    assert not (runtime_dir / ".git").exists()
    assert not (runtime_dir / ".venv").exists()
    assert not (runtime_dir / ".codex").exists()
    assert not (runtime_dir / ".agents").exists()
    assert not (runtime_dir / "SKILL.md").exists()
    assert not (runtime_dir / "adapters" / "claude-code" / "skills").exists()
    assert sorted(path.relative_to(skill_dir).as_posix() for path in skill_dir.rglob("SKILL.md")) == ["SKILL.md"]
    assert (codex_home / "agents" / "scholar-writer.toml").exists()
    assert "学术写作助手" in (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    uninstall = run_script("uninstall-codex.sh", codex_home)

    assert uninstall.returncode == 0, uninstall.stderr
    assert not skill_dir.exists()
    assert not (codex_home / "agents" / "scholar-writer.toml").exists()


def test_installed_wrapper_sets_runtime_and_runs_help(tmp_path):
    codex_home = tmp_path / "codex-home"
    install = run_script("install-codex.sh", codex_home)
    assert install.returncode == 0, install.stderr

    wrapper = codex_home / "skills" / "scholar-writing" / "bin" / "scholar-writing"
    content = wrapper.read_text(encoding="utf-8")
    assert "UV_CACHE_DIR" in content

    result = subprocess.run(
        [str(wrapper), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "ScholarWriting deterministic workflow CLI" in result.stdout


def test_install_stops_when_previous_skill_payload_exists(tmp_path):
    codex_home = tmp_path / "codex-home"
    stale_file = codex_home / "skills" / "scholar-writing" / "skills" / "pipeline" / "SKILL.md"
    stale_file.parent.mkdir(parents=True)
    stale_file.write_text("old payload\n", encoding="utf-8")

    install = run_script("install-codex.sh", codex_home)

    assert install.returncode == 10
    assert "Existing ScholarWriting installation detected" in install.stderr
    assert "rerun with --replace" in install.stderr
    assert stale_file.exists()


def test_install_replaces_previous_skill_payload_when_explicitly_allowed(tmp_path):
    codex_home = tmp_path / "codex-home"
    stale_file = codex_home / "skills" / "scholar-writing" / "skills" / "pipeline" / "SKILL.md"
    stale_file.parent.mkdir(parents=True)
    stale_file.write_text("old payload\n", encoding="utf-8")

    install = run_script("install-codex.sh", codex_home, "--replace")

    assert install.returncode == 0, install.stderr
    assert not stale_file.exists()


def test_repository_does_not_expose_install_shim_as_root_skill():
    assert not (REPO_ROOT / "SKILL.md").exists()


def test_install_can_finalize_generic_skill_install_location(tmp_path):
    codex_home = tmp_path / "codex-home"
    generic_skill_dir = codex_home / "skills" / "scholar-writing"
    ignore = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache")
    shutil.copytree(REPO_ROOT, generic_skill_dir, ignore=ignore)

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    result = subprocess.run(
        ["bash", str(generic_skill_dir / "scripts" / "install-codex.sh"), "--no-sync"],
        cwd=generic_skill_dir,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (generic_skill_dir / "SKILL.md").exists()
    assert (generic_skill_dir / "runtime" / "pyproject.toml").exists()
    assert (generic_skill_dir / "bin" / "scholar-writing").exists()
    assert not (generic_skill_dir / "runtime" / "adapters" / "claude-code" / "skills").exists()
    assert not (generic_skill_dir / "scripts" / "install-codex.sh").exists()
