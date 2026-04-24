# Schema 目录

本目录包含 ScholarWriting 系统所有数据类型的 JSON Schema 定义和 Markdown 校验规则。

## 文件说明

| 文件 | 校验目标 | 校验方式 |
|------|---------|---------|
| config.schema.yaml | config.yaml | JSON Schema + 语义校验 |
| manifest.schema.yaml | materials/manifest.yaml | JSON Schema + 文件存在性 |
| scores.schema.yaml | scores.yaml | JSON Schema + 状态机校验 |
| dependency_graph.schema.yaml | planning/dependency_graph.yaml | JSON Schema + DAG 校验 |
| outline.schema.yaml | planning/outline.md (frontmatter) | JSON Schema |
| claim_registry.schema.yaml | planning/claim_registry.md (frontmatter) | JSON Schema |
| review_report.schema.yaml | reviews/*_R*.md (frontmatter) | JSON Schema + 维度校验 |
| taskpack.schema.yaml | `scholar-writing taskpack` 输出 | JSON Schema |
| review_result.schema.yaml | `advance --event-file` 的 review_result 事件 | JSON Schema |
| revision_log.schema.yaml | revisions/*.yaml 修订日志 | JSON Schema |
| markdown_rules.yaml | Markdown 正文 | 正则模式匹配 |

## 状态机要点

`scores.schema.yaml` 同时支持机器状态和人类可读摘要：

- `phase`：当前流程阶段，例如 `initialized`、`section_reviewing`、`section_revision`、`complete`、`blocked`。
- `summary` / `notes`：面向用户的进度说明。
- `last_action`：最近一次 controller 动作。
- `next_action`：下一步动作，动作枚举与 CLI/controller 保持一致。
- `blocked_reason`：需要用户介入时的阻塞原因。
- `sections[*].inner_scores`：支持结构化轮次评分对象，包含 `round`、维度分、`weighted` 和 `flagged`。

Codex 工作流通过以下命令读取和推进状态：

```bash
uv run scholar-writing next <project_dir> --format json
uv run scholar-writing taskpack <project_dir> --format json
uv run scholar-writing advance <project_dir> --event-file <review-result.yaml> --format json
```

## 使用方法

```bash
# 校验单个文件
uv run python scholar-writing/scripts/validate.py config config.yaml
uv run python scholar-writing/scripts/validate.py review_report reviews/round_1/02_立项依据_R1.md

# 批量校验项目
uv run python scholar-writing/scripts/validate.py all .

# JSON 输出（供 Pipeline 程序化调用）
uv run python scholar-writing/scripts/validate.py config config.yaml --format json

# 严格模式（warning 也视为错误）
uv run python scholar-writing/scripts/validate.py all . --strict
```

## 扩展

- P2 计划：增加 R8 专家评审模拟的 schema（expert_review.schema.yaml）
- change log 已有 `revision_log.schema.yaml`，后续可继续扩展全文级 revision summary
- 新增模板类型时，在 markdown_rules.yaml 中增加对应的规则组
