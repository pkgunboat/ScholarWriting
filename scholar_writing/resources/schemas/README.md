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
| reference_registry.schema.yaml | `scholar_writing/resources/config/reference_registry.yaml` | JSON Schema |
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

## References 与 Taskpack

`reference_registry.schema.yaml` 校验框架内置写作规则的索引。Registry 中的路径必须使用相对路径，并指向 `scholar_writing/resources/references/` 下的实际文件。

`taskpack.schema.yaml` 支持 `reference_inputs`：

- `required`：本轮任务必须读取的规则。
- `section_specific`：目标章节对应的句式或结构规则。
- `optional`：上下文预算允许时读取的辅助规则。

`review_result.schema.yaml` 和 `revision_log.schema.yaml` 支持 `reference_basis`，用于记录审阅问题或修订动作依据的规则来源。

## 使用方法

```bash
# 校验单个文件
uv run python scholar_writing/resources/scripts/validate.py config config.yaml
uv run python scholar_writing/resources/scripts/validate.py review_report reviews/round_1/02_立项依据_R1.md

# 批量校验项目
uv run python scholar_writing/resources/scripts/validate.py all .

# JSON 输出（供 Pipeline 程序化调用）
uv run python scholar_writing/resources/scripts/validate.py config config.yaml --format json

# 严格模式（warning 也视为错误）
uv run python scholar_writing/resources/scripts/validate.py all . --strict
```

## 扩展

- P2 计划：增加 R8 专家评审模拟的 schema（expert_review.schema.yaml）
- change log 已有 `revision_log.schema.yaml`，后续可继续扩展全文级 revision summary
- 新增模板类型时，在 markdown_rules.yaml 中增加对应的规则组
- 新增 reference 文件时，同步更新 `reference_registry.yaml`，并添加 selector/taskpack 测试
