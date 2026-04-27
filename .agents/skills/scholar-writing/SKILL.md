---
name: scholar-writing
description: 学术写作助手，用于国自然申报书、论文、申报书起草、初稿审阅、多 agent 写作，以及“写作-审阅-修订”循环优化。
---

# 学术写作助手

本 skill 的机器 ID 是 `scholar-writing`。面向中文用户时，优先称为“学术写作助手”。

当用户要求进行学术写作、国自然/NSFC 申报书写作、论文起草、申报书审阅、初稿优化，或希望自动推进“写作-审阅-修订”循环时，使用本 skill。

## 基本规则

- 以 `uv run scholar-writing next <project_dir> --format json` 作为下一步动作的确定性来源。
- 在委派给 agent 前，先用 `uv run scholar-writing taskpack <project_dir> --format json` 生成本轮任务包。
- 用 `uv run scholar-writing advance <project_dir> --format json` 把计算出的下一步动作写回 `scores.yaml`。
- 把 `scores.yaml` 当作流程状态源，不要只根据自然语言描述推断循环进度。
- 把 `taskpack.reference_inputs` 视为写作、审阅和修订的质量规则。传递给 agent 时，应说明这些文件是框架规则，不是用户提供的事实证据。
- 调用 agent 前必须检查 `reference_inputs`。先读取 `required`，再读取 `section_specific`，上下文预算允许时再读取 `optional`。
- 路径应相对用户的写作项目目录解释，不要默认相对本 skill 目录。
- 除非用户明确要求完整规则审计，不要一次性读取 `scholar-writing/references/` 下的全部文件。
- 不要在平台中性入口里硬编码某个框架的 agent 调用语法。若当前运行环境支持 custom agents 或 subagents，应按该环境的原生机制委派。
- 只有当任务边界清晰、并行收益明显时才使用 subagents。强顺序依赖或状态推进紧密耦合的步骤留在主 agent 中执行。
- 普通 major/minor 修改意见可以自动处理。涉及核心论点变化、大范围重构、关键事实改写或跨章节连锁影响时，编辑章节前必须先向用户确认。

## 必须执行的循环

1. 确认写作项目目录。如果用户没有提供，使用当前仓库；如果当前目录明显不是写作项目，则询问目标目录。
2. 执行：

   ```bash
   uv run scholar-writing next <project_dir> --format json
   uv run scholar-writing taskpack <project_dir> --format json
   ```

3. 检查任务包中的 `reference_inputs`。这些文件是 controller 选择出的质量规则。
4. 按返回的 `action` 推进：

   - `run_architect`：使用规划 agent 产出或更新 `planning/outline.md`、`planning/claim_registry.md` 和 `planning/dependency_graph.yaml`。
   - `run_writer`：使用写作 agent 完成 `sections/` 中的目标章节。
   - `run_reviewers`：使用审阅 agent；只有在用户要求多 agent 审阅或任务确实受益时，才并行运行独立审阅维度。
   - `run_revision`：使用修订 agent，并严格限制在任务包允许的写入边界内。
   - `ask_user`：停止自动推进，向用户索取缺失输入或必要确认。

5. 每次 agent 输出后，都要更新或核对 `scores.yaml`，再重新运行 `uv run scholar-writing next <project_dir> --format json`。
6. 在声称流程完成前，执行：

   ```bash
   uv run pytest -q
   uv run scholar-writing validate <project_dir> --format json
   ```

## 支持的项目输入形态

- `from_materials`：存在 `materials/manifest.yaml`，从规划开始。
- `from_outline`：存在 `planning/outline.md`，从章节写作开始。
- `from_draft`：存在 `sections/*.md`，从审阅和修订开始。

当 `config.yaml` 使用 `input_mode: auto` 时，CLI 按以下优先级识别实际模式：已有章节初稿、已有提纲、已有材料。

## 开发者调试

在 ScholarWriting 源码仓库内开发时，本 repo-local skill 是平台中性的调试入口。Codex 可以配合源码中的 `.codex/agents` 和源码 CLI 调试；Claude Code、opencode 等其他能发现 `.agents/skills` 的框架，也应按各自的原生 agent/subagent 机制消费同一套任务包。

推荐的本地 smoke 命令：

```bash
uv run scholar-writing next examples/from-materials --format json
uv run scholar-writing next examples/from-outline --format json
uv run scholar-writing next examples/from-draft --format json
uv run scholar-writing taskpack examples/from-draft --format json
uv run pytest -q
```

预期首个动作：

- `examples/from-materials` -> `run_architect`
- `examples/from-outline` -> `run_writer`
- `examples/from-draft` -> `run_reviewers`

如果要测试 Codex custom agent 文案或 handoff 契约，可以直接使用 `.codex/agents`；这属于 Codex 专用适配层，不是本 `.agents` skill 的通用语义。
