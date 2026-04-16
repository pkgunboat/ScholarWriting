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
| markdown_rules.yaml | Markdown 正文 | 正则模式匹配 |

## 使用方法

```bash
# 校验单个文件
python3 scripts/validate.py config config.yaml
python3 scripts/validate.py review_report reviews/round_1/02_立项依据_R1.md

# 批量校验项目
python3 scripts/validate.py all .

# JSON 输出（供 Pipeline 程序化调用）
python3 scripts/validate.py config config.yaml --format json

# 严格模式（warning 也视为错误）
python3 scripts/validate.py all . --strict
```

## 扩展

- P2 计划：增加 R8 专家评审模拟的 schema（expert_review.schema.yaml）
- P2 计划：增加 change_logs 和 summaries 的校验
- 新增模板类型时，在 markdown_rules.yaml 中增加对应的规则组
