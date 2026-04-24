# Codex 架构说明

ScholarWriting 的 Codex 适配采用三层结构。

## 共享核心

`scholar_writing/` 是平台无关 Python package，负责：

- 路径定位。
- 默认配置与项目配置合并。
- Schema 加载与校验。
- 输入模式检测。
- `scores.yaml` 状态读写。
- next action 计算。
- task pack 生成。
- reference registry 加载与规则选择。
- review result 事件推进。
- CLI 入口。

## Reference Registry

`scholar-writing/config/reference_registry.yaml` 是写作规则资料的索引。它把 `scholar-writing/references/` 下的风格指南、国自然结构、去 AI 规则和句式模板映射到 action、agent role、项目类型和审阅维度。

Controller 通过 `scholar_writing.core.references.select_references()` 为每个 task pack 生成 `reference_inputs`：

```yaml
reference_inputs:
  required: []
  section_specific: []
  optional: []
```

这些 references 是质量规则。用户事实仍来自 `materials/`、`planning/`、`sections/` 和用户输入。

## Codex Adapter

Codex adapter 包含：

- `.agents/skills/scholar-writing/SKILL.md`
- `.codex/agents/scholar-architect.toml`
- `.codex/agents/scholar-writer.toml`
- `.codex/agents/scholar-reviewer.toml`
- `.codex/agents/scholar-revision.toml`

Codex skill 先调用 controller 获取确定性动作：

```bash
uv run scholar-writing next <project_dir> --format json
```

然后根据返回的 action 决定是否调用 custom agents。

Agent handoff 使用：

```bash
uv run scholar-writing taskpack <project_dir> --format json
```

Task pack 同时携带输入、输出边界和 `reference_inputs`。Codex custom agent 在写作、审阅或修订前应先读取 `required`，再读取 `section_specific`，最后按上下文预算读取 `optional`。

审阅结果等确定性事件使用 YAML event file 推进：

```bash
uv run scholar-writing advance <project_dir> --event-file tests/fixtures/review-low.yaml --format json
```

`advance` 会更新 `scores.yaml`，低分审阅进入 `section_revision`，高分审阅进入 `complete` 或下一章节，高风险审阅通过 `ask_user` 暂停。

## Legacy Claude Code Adapter

`scholar-writing/skills/` 暂时保留为 Claude Code 风格入口和 prompt 资料库。`scholar-writing/skills/pipeline/SKILL.md` 已标记为 legacy adapter。后续应逐步把其中的角色指令抽取到共享 prompt 包，避免核心逻辑继续绑定 Claude Code 的 `Agent(...)` 语义。
