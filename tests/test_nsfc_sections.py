from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SECTION_FILES = {
    "摘要": "sections/01_摘要.md",
    "立项依据": "sections/02_立项依据.md",
    "研究内容": "sections/03_研究内容.md",
    "研究方案": "sections/04_研究方案.md",
    "可行性分析": "sections/05_可行性分析.md",
    "创新点": "sections/06_创新点.md",
    "研究基础": "sections/07_研究基础.md",
}


def test_nsfc_writer_outputs_match_base_template_section_files():
    for section_name, expected_path in EXPECTED_SECTION_FILES.items():
        config_path = REPO_ROOT / "scholar-writing" / "skills" / "writer" / "nsfc" / section_name / "config.yaml"
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        section_outputs = [
            item["path"]
            for item in data["parameters"]["outputs"]
            if item["name"] == "section"
        ]
        assert section_outputs == [expected_path]
        assert expected_path in data["guardrails"]["allowed_write_files"]


def test_nsfc_base_template_declares_canonical_section_files():
    data = yaml.safe_load((REPO_ROOT / "scholar-writing" / "templates" / "nsfc" / "base.yaml").read_text(encoding="utf-8"))
    template_files = {section["name"]: section["file"] for section in data["sections"]}

    assert template_files == {
        name: path.removeprefix("sections/")
        for name, path in EXPECTED_SECTION_FILES.items()
    }
