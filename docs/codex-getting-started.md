# Codex 使用指南

本仓库第一阶段采用 repo 内 Codex workflow，不要求先安装 plugin。

## 准备环境

```bash
uv sync
uv run pytest -q
```

## 检查下一步动作

```bash
uv run scholar-writing next examples/demo-nsfc-proposal --format json
```

返回的 `action` 是 Codex 工作流的确定性入口。

## 检查任务包与规则资料

```bash
uv run scholar-writing taskpack examples/from-outline --format json
```

输出中的 `reference_inputs` 是本轮 agent 应读取的质量规则。它们来自 `scholar-writing/references/`，包括中文学术风格、国自然结构、去 AI 痕迹规则和章节句式模板。

用户通常不需要手动打开这些文件。Codex skill 会先生成 taskpack，再把 `reference_inputs` 作为写作、审阅或修订规则传给 custom agent。

## 常用 CLI

```bash
uv run scholar-writing init examples/scholar-writing-smoke --type nsfc --mode auto
uv run scholar-writing validate examples/from-materials --format json
uv run scholar-writing status examples/from-draft --format json
uv run scholar-writing next examples/from-outline --format json
uv run scholar-writing taskpack examples/from-outline --format json
uv run scholar-writing advance examples/from-draft --format json
```

三种入口 fixture：

- `examples/from-materials`：应返回 `run_architect`。
- `examples/from-outline`：应返回 `run_writer`。
- `examples/from-draft`：应返回 `run_reviewers`。

## 在 Codex 中触发

可以直接要求：

```text
使用 scholar-writing 审阅优化 examples/demo-nsfc-proposal。
```

Codex 应读取 `.agents/skills/scholar-writing/SKILL.md`，先运行 CLI 获取 next action，再按需使用 `.codex/agents/` 下的 4 类 custom agents。

## 当前边界

- 当前形态是 repo workflow，plugin 分发属于后续阶段。
- CLI 负责确定性状态判断，LLM agent 负责写作、审阅和修订。
- `reference_inputs` 负责把框架内置写作规则接入 agent handoff。
- `scores.yaml` 是状态源。
- critical 或大范围修订必须先确认。
