from pathlib import Path

from scholar_writing.core.paths import find_repo_root
from scholar_writing.core.schema import validate_data


def test_review_result_accepts_reference_basis():
    repo_root = find_repo_root(Path(__file__))
    payload = {
        "kind": "review_result",
        "data": {
            "section": "02_立项依据",
            "round": 1,
            "scores": {"de_ai": 68},
            "issues": [
                {
                    "severity": "major",
                    "message": "开头使用公式化背景句，信息密度低。",
                    "reference_basis": [
                        {"id": "deai_zh", "rule": "公式化开头模式"},
                        {"id": "style_zh"},
                    ],
                }
            ],
        },
    }

    assert validate_data("review_result", payload, repo_root) == []


def test_revision_log_accepts_reference_basis():
    repo_root = find_repo_root(Path(__file__))
    payload = {
        "section": "02_立项依据",
        "round": 1,
        "risk_level": "major",
        "changes": [
            {
                "summary": "重写开篇段落，直接切入具体问题。",
                "reason": "降低公式化开头痕迹。",
                "reference_basis": [
                    {"id": "deai_zh", "rule": "公式化开头模式"},
                    {"id": "style_zh"},
                ],
            }
        ],
    }

    assert validate_data("revision_log", payload, repo_root) == []
