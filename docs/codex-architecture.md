# Codex 架构说明

ScholarWriting 的 Codex 适配采用“本机安装 + 用户项目运行”的结构。

安装脚本会把框架 runtime 复制到 Codex skill 目录，并把 custom agents 安装到 Codex agents 目录。用户日常使用时用 Codex 打开自己的写作项目，controller 通过安装 runtime 读取 schemas、references、prompts 和 templates。

仓库根目录的 `SKILL.md` 是自然语言安装入口。用户在 Codex 中提供仓库地址、本机仓库路径，或直接说 `scholar writing` 并要求安装或卸载时，Codex 可以根据该入口执行 `scripts/install-codex.sh` 或 `scripts/uninstall-codex.sh`。

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

## Repo-local Skill 与 Codex Adapter

源码仓库中的 `.agents/skills/scholar-writing/SKILL.md` 是平台通用 repo-local skill。Codex、Claude Code、opencode 等能发现 `.agents/skills` 的框架都可能读取它，因此这里不应写成 Codex 专属工作流。

源码仓库中的 Codex adapter 包含：

- `.codex/agents/scholar-architect.toml`
- `.codex/agents/scholar-writer.toml`
- `.codex/agents/scholar-reviewer.toml`
- `.codex/agents/scholar-revision.toml`

一键安装后，Codex 使用安装目录中的 global skill 和 agents：

```text
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/
${CODEX_HOME:-$HOME/.codex}/agents/scholar-*.toml
```

安装目录中的 `bin/scholar-writing` 会设置 `SCHOLAR_WRITING_RUNTIME`，因此 controller 可以在用户项目目录中运行，同时读取安装 runtime 中的框架资源。

Codex skill 先调用 controller 获取确定性动作：

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing next <project_dir> --format json
```

然后根据返回的 action 决定是否调用 custom agents。

Agent handoff 使用：

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing taskpack <project_dir> --format json
```

Task pack 同时携带输入、输出边界和 `reference_inputs`。Codex custom agent 在写作、审阅或修订前应先读取 `required`，再读取 `section_specific`，最后按上下文预算读取 `optional`。

审阅结果等确定性事件使用 YAML event file 推进：

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing advance <project_dir> --event-file <review-result.yaml> --format json
```

`advance` 会更新 `scores.yaml`，低分审阅进入 `section_revision`，高分审阅进入 `complete` 或下一章节，高风险审阅通过 `ask_user` 暂停。

## Legacy Claude Code Adapter

`scholar-writing/skills/` 暂时保留为 Claude Code 风格入口和 prompt 资料库。`scholar-writing/skills/pipeline/SKILL.md` 已标记为 legacy adapter。后续应逐步把其中的角色指令抽取到共享 prompt 包，避免核心逻辑继续绑定 Claude Code 的 `Agent(...)` 语义。
