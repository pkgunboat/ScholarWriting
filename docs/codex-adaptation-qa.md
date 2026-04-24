# Codex 适配方向 QA 记录

本文档用于记录 ScholarWriting 从 Claude Code 设计迁移到 Codex App 使用时的方向讨论。它不是最终实施计划，而是把存疑项通过问答方式收敛为可执行判断。

## 背景

当前 review 已确认的核心问题：

- 仓库声明为多智能体学术写作框架，但 Codex 中不会自然触发多智能体。
- Codex 无法自动执行“写作 -> 审查 -> 修订 -> 再审查”的闭环。
- 现有 `scholar-writing/skills/pipeline/SKILL.md` 是 Claude Code 风格编排说明，依赖 `Agent`/`Bash` 等 Claude Code 语义。
- 仓库缺少 Codex 可发现的分发入口，例如 `.agents/skills/` 或 `.codex-plugin/plugin.json`。
- 状态文件、Schema、示例、writer 输出路径、测试路径存在多处契约漂移。

## 讨论目标

通过逐轮问答确定：

- Codex 适配的目标产品形态。
- 是否保留 Claude Code 兼容层。
- 多智能体应由 Codex custom agents、主入口 skill 显式调度，还是由脚本生成任务包后交给 Codex 执行。
- 自动优化循环应做到多自动，以及在哪些位置保留人工确认。
- 第一阶段改造的最小可用范围和验收标准。

## QA 记录

### Q1：Codex 适配的首要目标是什么？

**问题：** 在第一阶段，我们应该把目标定位成哪一种？

- A. Codex App 可安装插件：优先让用户能“安装后触发”，即使自动循环先做最小闭环。
- B. Repo 内 Codex workflow：优先在当前仓库开发/运行，通过 `.agents/skills` 和 `.codex/agents` 验证流程，暂不强调插件分发。
- C. 双轨兼容：同时保留 Claude Code 原入口，并新增 Codex plugin/repo workflow，但第一阶段工作量更大。

**用户回答：** B. Repo 内 Codex workflow。

**当前判断：** 第一阶段优先在当前仓库中跑通 Codex 原生工作流，不先追求插件化安装。改造重点应放在 `.agents/skills`、`.codex/agents`、项目内状态机、示例和测试闭环上。`.codex-plugin/plugin.json` 可作为第二阶段分发能力，不作为第一阶段阻塞项。

**影响范围：** 第一阶段优先新增 repo-local Codex 入口；文档重点改为“在仓库中启用和验证 Codex workflow”；测试以当前 worktree 可运行作为验收；插件分发暂缓。

**状态：** 已确认。

### Q2：多智能体粒度应该如何设计？

**问题：** 第一阶段应采用哪种 agent 粒度？

- A. 4 类通用 agents：`architect`、`writer`、`reviewer`、`revision`。入口 skill 根据任务传入章节类型和 reviewer 维度。
- B. 中等粒度 agents：`architect`、7 个 writer、1 个通用 reviewer、1 个 revision。先保留章节写作差异，审阅维度暂由任务参数控制。
- C. 贴近原设计的 18 个 agents：architect、7 writers、8 reviewers、revision、expert simulation。最接近项目愿景，但配置和验证成本最高。

**用户回答：** A. 4 类通用 agents。

**当前判断：** 第一阶段采用 4 类通用 Codex agents：`architect`、`writer`、`reviewer`、`revision`。专业差异先通过任务包参数、章节模板、checklist 和 prompt references 注入，而不是一开始拆成 18 个 agent 配置。这样能更快验证 Codex 是否能稳定触发多 agent 和自动循环。

**影响范围：** `.codex/agents` 初期只需要 4 个配置文件；入口 skill 需要负责把章节类型、writer 策略、reviewer 维度传入 agent；后续可以在闭环稳定后逐步拆分 R1-R8 和 7 个 writers。

**状态：** 已确认。

### Q3：自动优化循环中是否需要人工确认修订？

**问题：** 第一阶段的“写作 -> 审查 -> 修订 -> 再审查”循环，在 Revision agent 修改章节正文前，是否需要人工确认？

- A. 每轮修订前都要用户确认：最安全，但自动化体验弱，容易中断。
- B. 仅 critical/大范围改动前确认：普通 major/minor 问题自动修，涉及核心论点、研究内容增删、关键数据变化时确认。
- C. 全自动修订直到达到阈值或超轮次：最接近自动优化框架，但需要强状态机、diff 和回滚/审计记录支撑。

**用户回答：** B. 仅 critical/大范围改动前确认。

**当前判断：** 第一阶段采用风险分级自动修订策略。Revision agent 可以自动处理普通 major/minor 问题；当修改涉及 critical 问题、核心论点变化、研究内容增删、关键数据变化、章节结构大调整或跨章节影响较大时，循环应暂停并请求用户确认。所有自动修订必须写入 change log，并保留原文摘要、修改原因和受影响章节。

**影响范围：** loop controller 需要识别 `requires_user_confirmation`；Revision agent 需要输出风险级别和影响分析；`scores.yaml` 需要记录暂停原因；change log 需要成为自动修订的审计依据。

**状态：** 已确认。

### Q4：第一阶段优先支持哪些输入模式？

**问题：** 为了尽快验证 Codex 多 agent 和自动循环，第一阶段应先支持哪些入口？

- A. 只支持 `from_outline`：用户已有大纲，从章节写作开始，最适合验证 writer -> reviewer -> revision 闭环。
- B. 支持 `from_outline` + `from_draft`：既能从大纲写作，也能对已有初稿审阅优化，覆盖最常见的 Codex 使用场景。
- C. 三种模式都支持：`from_materials`、`from_outline`、`from_draft`，完整但会把素材解析、manifest、规划质量也纳入第一阶段。

**用户回答：** C. 三种模式都支持。

**当前判断：** 第一阶段需要同时支持 `from_materials`、`from_outline`、`from_draft`。这意味着 Codex workflow 不能只做章节写作/审阅闭环，还必须覆盖 Architect 规划、manifest 规范化、从初稿抽取 claim registry、从大纲补全依赖图等入口准备步骤。

**影响范围：** 第一阶段必须修复 materials manifest Schema 与示例漂移；Architect agent 进入 P0 范围；需要至少 3 个可验证 fixture；loop controller 的 `detect_input_mode` 必须可靠；文档需要同时说明三种启动方式。

**状态：** 已确认。

### Q5：`scores.yaml` 应定位为机器状态机还是人类进度报告？

**问题：** 自动循环需要状态文件。`scores.yaml` 第一阶段应如何定位？

- A. 严格机器状态机：字段强约束，所有状态转移由脚本校验；人类阅读性次要。
- B. 机器状态机 + 人类可读摘要：核心字段严格，额外保留 summary / notes / last_action 方便用户理解。
- C. 人类进度报告为主：允许自由结构，状态判断更多由 Codex 主 agent 解释。

**用户回答：** B. 机器状态机 + 人类可读摘要。

**当前判断：** `scores.yaml` 应作为自动循环的可靠状态源，同时保留用户可读进度信息。核心字段如 `phase`、`sections[*].status`、`current_round`、`scores`、`next_action` 应由 Schema 严格校验；辅助字段如 `summary`、`notes`、`last_action`、`blocked_reason` 可帮助用户理解当前状态。

**影响范围：** `scores.schema.yaml` 需要改为结构化状态机；loop controller 应负责状态转移；Codex 主 agent 读取 `next_action` 继续工作；用户可以直接打开 `scores.yaml` 理解进度和阻塞原因。

**状态：** 已确认。

### Q6：是否接受新增 Python loop controller？

**问题：** 为了让 Codex 稳定执行自动循环，是否接受新增确定性 Python 控制器？

- A. 接受。新增脚本负责状态机、下一步动作、评分聚合、产物校验；Codex agents 负责写作/审阅/修订。
- B. 尽量不新增控制器。主要靠 Codex 入口 skill 和 prompt 维护循环，脚本只做校验。
- C. 折中。先新增轻量 `next_action` 脚本，不做完整 pipeline controller，后续再扩展。

**用户回答：** A. 接受新增 Python loop controller。

**当前判断：** 第一阶段应新增确定性 Python loop controller。控制器负责读取配置、检测输入模式、维护 `scores.yaml`、计算下一步动作、聚合评分、校验产物和判断是否继续循环。Codex agents 负责实际写作、审阅和修订。这样能降低主入口 skill 的不确定性，并让自动循环可测试。

**影响范围：** 需要新增 `run_pipeline.py` 或等价控制器模块；测试应覆盖状态转移和 next action；Codex 入口 skill 主要调用控制器、派发 agent、回收产物；自动循环不再完全依赖自然语言 prompt。

**状态：** 已确认。

### Q7：是否长期保留 Claude Code 原生入口？

**问题：** Codex 改造后，Claude Code 原生入口应如何处理？

- A. 保留并标记为 legacy/claude adapter：不主动重构，只保证文档说明边界。
- B. 双端同步维护：Claude Code 和 Codex 两套入口都作为一等公民，改动时都要同步测试。
- C. 逐步迁移到平台无关核心：保留 Claude Code 兼容，但把主架构迁到共享 prompts/scripts/schemas，Claude 和 Codex 都只是 adapter。

**用户回答：** C. 逐步迁移到平台无关核心。

**当前判断：** 长期方向应是“平台无关核心 + 平台 adapter”。共享核心包含 prompts、templates、schemas、scripts、loop controller 和 examples；Codex 与 Claude Code 分别作为 adapter。Claude Code 原生入口不删除，但逐步降级为 adapter，避免继续把核心逻辑写死在 Claude Code 的 `Agent` 工具语义里。

**影响范围：** 目录结构应逐步拆出 `prompts/`、`adapters/codex/`、`adapters/claude-code/` 或等价分层；`scholar-writing/skills/pipeline/SKILL.md` 保留但标记为 Claude adapter；Codex 入口不直接复制 Claude pipeline，而是调用共享 controller 和 prompt 包。

**状态：** 已确认。

## 已确认方向摘要

- 第一阶段目标：Repo 内 Codex workflow，而不是优先插件分发。
- 第一阶段 agent 粒度：4 类通用 agents，分别是 architect、writer、reviewer、revision。
- 自动修订策略：普通问题自动修，critical/大范围/高风险变更前请求用户确认。
- 输入模式：第一阶段同时支持 `from_materials`、`from_outline`、`from_draft`。
- `scores.yaml` 定位：机器状态机 + 人类可读摘要。
- 自动循环实现：接受新增 Python loop controller。
- 长期架构：平台无关核心 + Codex/Claude Code adapters。

## 候选整体方案

### 方案 A：轻量 Codex Workflow Adapter

先新增 `.agents/skills`、`.codex/agents` 和一个轻量 `next_action.py`，尽量少改现有目录。Claude Code 原目录基本保留。

优点：改动小，能较快验证 Codex 触发和 subagent 调度。

缺点：核心逻辑仍分散在 Claude Code 风格 `SKILL.md` 中，长期会继续漂移。

### 方案 B：共享核心 + Codex Adapter 优先

第一阶段就把关键 prompt/状态机/路径契约抽成共享核心，新增 Codex adapter 调用共享核心。Claude Code 入口保留为 legacy，但后续可迁移到同一核心。

优点：符合已确认的长期方向，能同时解决自动循环和契约漂移。

缺点：第一阶段改动面比方案 A 大，需要更明确的模块边界和测试。

### 方案 C：完整平台化重构

直接重构为平台无关 package，Codex 和 Claude Code 都只是薄 adapter，同时补完整 CLI、plugin、agents、端到端示例。

优点：最终形态最干净。

缺点：成本最高，第一阶段容易陷入大重构，短期难验证用户痛点。

**用户选择：** 方案 C. 完整平台化重构。

**当前判断：** 后续设计主线改为完整平台化重构。ScholarWriting 应重构为平台无关 package：共享核心负责配置、状态机、模板、Schema、prompt 包、loop controller 和 CLI；Codex 与 Claude Code 都作为 adapter 接入共享核心。Codex 的 repo workflow、custom agents 和后续 plugin 分发都应建立在该共享核心之上，而不是作为临时补丁。

**影响范围：** 第一阶段设计需要覆盖 package/CLI、adapter 边界、目录重组、端到端示例、测试矩阵和迁移策略。短期工作量增加，但能最大程度避免继续积累平台绑定和契约漂移。

## 待提问池

- 自动循环是否允许 Codex 在没有人工确认的情况下修改章节正文？
- 多智能体粒度是先做 4 类通用 agents，还是直接拆成 18 个专业 agents？
- 第一阶段是否需要支持 `from_materials`，还是先只跑通 `from_outline` / `from_draft`？
- `scores.yaml` 是作为人可读进度文件，还是作为严格机器状态机文件？
- 是否接受新增 Python loop controller，还是希望尽量保持纯 Codex skill/prompt 工作流？
- 是否需要长期保留 Claude Code 原生安装方式？
