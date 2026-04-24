from .project import detect_input_mode


def section_weighted_score(scores, config):
    """Compute section weighted score from reviewer dimension scores."""
    weights = config.get("score_weights", {}).get("section", {})
    if not scores:
        return 0
    if not weights:
        return sum(scores.values()) / len(scores)
    total = 0
    used_weight = 0
    for key, value in scores.items():
        weight = weights.get(key, 0)
        total += value * weight
        used_weight += weight
    if used_weight == 0:
        return sum(scores.values()) / len(scores)
    return round(total / used_weight, 2)


def has_critical_issue(issues):
    """Return whether review issues contain a critical issue."""
    return any(str(issue.get("severity", "")).lower() == "critical" for issue in issues or [])


def all_sections_approved(state):
    """Return whether all known sections are approved."""
    sections = state.get("sections", {})
    return bool(sections) and all(section.get("status") == "approved" for section in sections.values())


def next_action(project_dir, config, state):
    """Compute the next deterministic workflow action."""
    if state.get("blocked_reason"):
        return {
            "action": "ask_user",
            "reason": state["blocked_reason"],
        }

    phase = state.get("phase")
    if phase in {"revision", "section_revision", "global_revision"}:
        revision = state.get("revision", {})
        if revision.get("requires_user_confirmation"):
            return {
                "action": "ask_user",
                "reason": revision.get("confirmation_reason", "修订涉及高风险变更，需要用户确认。"),
            }
        return {
            "action": "run_revision",
            "reason": "当前状态要求根据审阅意见执行修订。",
        }

    input_mode = detect_input_mode(project_dir, config)
    if input_mode == "from_materials":
        return {
            "action": "run_architect",
            "input_mode": input_mode,
            "reason": "检测到 materials 输入，需要先生成规划产物。",
        }
    if input_mode == "from_outline":
        return {
            "action": "run_writer",
            "input_mode": input_mode,
            "reason": "检测到 planning/outline.md，可进入章节写作。",
        }
    if input_mode == "from_draft":
        return {
            "action": "run_reviewers",
            "input_mode": input_mode,
            "reason": "检测到 sections 初稿，可进入审阅优化。",
        }

    return {
        "action": "ask_user",
        "input_mode": input_mode,
        "reason": "未检测到 materials、outline 或 sections，需要用户补充输入。",
    }


def advance_state(state, config, event=None):
    """Advance workflow state from a deterministic event."""
    updated = dict(state)
    event = event or {}
    kind = event.get("kind")

    if kind == "review_result":
        data = event.get("data", {})
        section_name = data.get("section")
        if not section_name:
            updated["blocked_reason"] = "review_result 缺少 section。"
            updated["next_action"] = {"action": "ask_user", "reason": updated["blocked_reason"]}
            return updated

        sections = dict(updated.get("sections", {}))
        section = dict(sections.get(section_name, {"status": "pending", "current_round": 0}))
        scores = data.get("scores", {})
        weighted = section_weighted_score(scores, config)
        round_no = data.get("round", section.get("current_round", 0) + 1)
        issues = data.get("issues", [])

        section["current_round"] = round_no
        section["rounds_used"] = max(section.get("rounds_used", 0), round_no)
        section["current_score"] = weighted
        section["last_reviewer_scores"] = scores
        section.setdefault("inner_scores", []).append({
            "round": round_no,
            **scores,
            "weighted": weighted,
            "flagged": [issue.get("message", "") for issue in issues if issue.get("severity")],
        })

        threshold = config.get("convergence", {}).get("section_score_threshold", 80)
        critical = has_critical_issue(issues)
        if weighted >= threshold and not critical:
            section["status"] = "approved"
            updated["revision"] = {"requires_user_confirmation": False}
            updated["phase"] = "complete" if len(sections) <= 1 else "section_writing"
            updated["next_action"] = {
                "action": "stop_complete" if len(sections) <= 1 or all_sections_approved({"sections": {**sections, section_name: section}}) else "run_writer",
                "reason": "章节评分达到阈值并已收敛。",
            }
        else:
            section["status"] = "revising"
            updated["phase"] = "section_revision"
            updated["revision"] = {
                "section": section_name,
                "requires_user_confirmation": critical,
                "confirmation_reason": "critical issue requires user confirmation" if critical else None,
                "issues": issues,
            }
            updated["next_action"] = next_action(".", config, updated)

        sections[section_name] = section
        updated["sections"] = sections
        updated["last_action"] = "record_review_result"
        return updated

    updated["next_action"] = {"action": "advance_state", "reason": "无事件，仅记录状态推进。"}
    updated["last_action"] = "advance_state"
    return updated
