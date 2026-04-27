# Codex 适配审查与改进方案

本文档面向一个具体问题：ScholarWriting 当前设计基于 Claude Code 的 Skill/Agent 机制，但用户希望将它作为 Codex App 可安装、可触发、可多智能体运行、可自动迭代的学术写作框架使用。

结论先行：当前仓库的核心 Prompt、模板、审阅维度和写作方法论有价值，但还没有完成从“Claude Code 技能集合”到“Codex 可发现、可执行、可验证工作流”的产品化适配。Codex 中不会自然调用多智能体，也不会自动执行“写作-审查-修订”循环，主要不是模型能力问题，而是分发形态、agent 配置、编排器实现、状态机和文件契约都还没有以 Codex 为目标收口。

## 参考依据

本审查基于当前仓库文件和 OpenAI Codex 官方文档：

- Codex Skills：`https://developers.openai.com/codex/skills`
- Codex Customization：`https://developers.openai.com/codex/concepts/customization`
- Codex Subagents：`https://developers.openai.com/codex/subagents`
- Codex Build plugins：`https://developers.openai.com/codex/plugins/build`

官方要点对本项目的直接影响：

- Codex 的 repo-specific skills 应放在 `.agents/skills`，可安装分发应优先包装为 plugin。
- plugin 的必需入口是 `.codex-plugin/plugin.json`，技能目录通常位于 plugin 根目录的 `skills/`。
- Codex 的技能采用 progressive disclosure，只会先读取 `name`、`description` 等元数据，只有匹配任务时才加载完整 `SKILL.md`。
- Codex 支持 subagents，但不会因为文档中写了“多 Agent”就自动拆分；需要在工作流中显式要求，或提供 `.codex/agents/*.toml` 这样的 custom agents 配置。
- Codex subagents 是通过 Codex 的 agent 配置和调度能力运行，不等同于 Claude Code 的 `Agent` 工具。

## 当前水土不服的核心症状

### 痛点 1：声明多智能体，但 Codex 实际不会调用多智能体

仓库在 README 和 pipeline 中反复声明“18 个专业化 AI Agent”“R1/R2/R3 并行审阅”“Writer -> Reviewer -> Revision 循环”。但这些目前主要是说明文字和 Claude Code 风格伪代码，不是 Codex 可执行的 agent 配置。

当前证据：

- `adapters/claude-code/skills/pipeline/SKILL.md` 使用 `allowed-tools: [Read, Write, Edit, Bash, Agent]`，这是 Claude Code 工具模型，不是 Codex 的 custom agent 配置。
- pipeline 正文多处写 `Agent("architect", ...)`、`通过 Agent 工具调用 Writer Agent`、`通过 3 个并行 Agent 调用发出审阅请求`，但仓库没有 `.codex/agents/*.toml`。
- 仓库根目录没有 `.agents/skills/`，也没有 `.codex-plugin/plugin.json`。Codex 安装后很可能无法稳定发现这些技能，更不用说按角色调度。
- 各 writer/reviewer skill 都写了 `user-invocable: false` 和 “仅由 pipeline 编排器内部调用”，但 Codex 没有一个真正能识别并调用它们的 pipeline runtime。

根因：

- Claude Code 的 `Agent` 调度假设没有映射到 Codex 的 `spawn_agent` / custom agents。
- “角色定义”存在于 `SKILL.md`，但 Codex 需要明确的触发入口、agent 配置和调度策略。
- 当前 pipeline 是长文档式流程说明，不是一个 Codex 可以可靠执行的控制器。

### 痛点 2：Codex 无法触发“写作-审查”的自动优化循环

README 描述了章节内环和全文外环，但当前仓库没有可执行状态机。`scores.yaml` 只是被文档描述为状态追踪文件，`validate.py` 只是校验工具，二者没有被一个真实 runtime 串起来。

当前证据：

- `pipeline/SKILL.md` 里有 `FOR each section`、`WHILE round <= max_section_rounds`、`更新 scores.yaml` 等伪代码，但没有对应 Python/CLI 编排器。
- `scores.schema.yaml` 将 `inner_scores` 定义为 number 数组，而示例 `examples/demo-nsfc-proposal/scores.yaml` 实际使用对象数组，说明状态文件契约未稳定。
- `validate.py all` 查找 `config/default_config.yaml` 和 `state/scores.yaml`，但文档和示例项目使用项目根目录的 `config.yaml` 和 `scores.yaml`。
- 默认配置 `input_mode: auto` 与 `config.schema.yaml` 不兼容，默认配置本身无法通过当前校验。
- writer config 与模板的章节编号不一致，导致循环即使跑起来也会找错文件。例如模板定义 `01_摘要.md`、`02_立项依据.md`，但 writer config 把立项依据写到 `01_立项依据.md`，摘要写到 `07_摘要.md`。

根因：

- 自动循环目前是“Prompt 说明”，没有落成可运行的 loop controller。
- 状态文件、Schema、示例、writer 输出路径之间存在漂移。
- Codex App 不会自行从自然语言说明中持久执行一个跨轮次、跨文件、跨 agent 的循环，除非入口 skill 明确驱动并维护状态。

## P0 阻塞项

### P0-1：补 Codex 分发入口

当前仓库缺少 Codex 可安装分发结构。需要二选一：

- 作为 repo-specific workflow：新增 `.agents/skills/scholar-writing/SKILL.md`。
- 作为可安装插件：新增 `.codex-plugin/plugin.json`，并在根目录提供 `skills/`。

建议选择 plugin 形态，因为用户目标是“为 Codex App 安装本项目”。plugin 可以把 skills、agent 配置、MCP 或后续 App 入口打包成一个稳定安装单元。

最小目标：

- `.codex-plugin/plugin.json`
- `skills/scholar-writing/SKILL.md`
- `skills/scholar_writing/resources/references/`
- `skills/scholar_writing/resources/scripts/` 或明确引用仓库内脚本
- README 增加 Codex 安装与验证步骤

### P0-2：新增 Codex-native 入口 skill

不能直接把 Claude Code 版 `pipeline/SKILL.md` 暴露给 Codex。需要一个专门入口：

- 名称建议：`scholar-writing-codex`
- 触发描述要覆盖“写申报书”“审阅优化初稿”“国自然”“学术写作”“proposal”等用户真实表达。
- 明确 Codex 环境下如何选择模式：`from_materials`、`from_outline`、`from_draft`、`auto`。
- 明确何时使用 subagents，何时保持主 agent 串行。
- 明确所有文件路径都基于用户项目目录，而不是 skill 安装目录。

入口 skill 的关键职责：

- 读取或创建项目级 `config.yaml`。
- 调用或提示运行确定性校验。
- 为 writer/reviewer/revision 构造任务。
- 在 Codex 中显式触发 custom agents 或 subagents。
- 更新 `scores.yaml`。
- 在每一轮之后判断是否进入下一轮、停止、或请求人工介入。

### P0-3：定义 Codex custom agents

当前 “Architect / Writer / Reviewer / Revision” 都是 Claude Code 风格的 skill 文档，不会自动变成 Codex subagents。

建议新增 `.codex/agents/`：

- `scholar-architect.toml`
- `scholar-writer.toml`
- `scholar-reviewer-logic.toml`
- `scholar-reviewer-deai.toml`
- `scholar-reviewer-completeness.toml`
- `scholar-reviewer-consistency.toml`
- `scholar-reviewer-narrative.toml`
- `scholar-reviewer-feasibility.toml`
- `scholar-reviewer-format.toml`
- `scholar-revision.toml`
- `scholar-expert-sim.toml`

也可以先不拆到 18 个文件，而是先做 4 类 agents：

- `scholar_architect`
- `scholar_writer`
- `scholar_reviewer`
- `scholar_revision`

最小可行方案建议先做 4 类，避免配置爆炸。等循环跑通后，再把 reviewer 细分为 R1-R8。

### P0-4：实现或生成一个真实 loop controller

如果只靠一个长 Prompt 让主 agent 自觉循环，Codex 使用体验会不稳定。建议新增一个确定性控制器。

可选实现：

- `scholar_writing/resources/scripts/run_pipeline.py`
- `scholar_writing/resources/scripts/pipeline_state.py`
- `scholar_writing/resources/scripts/score_reports.py`

控制器不需要调用 LLM API。它只负责：

- 读取配置和模板。
- 计算下一步动作。
- 维护 `scores.yaml`。
- 生成给 Codex subagent 的任务包。
- 校验产物。
- 判断是否继续循环。

推荐把 LLM 写作/审阅仍交给 Codex agent，把状态转移、路径、轮次、评分聚合交给脚本。

### P0-5：统一章节文件契约

必须选择一个章节编号标准，并在模板、writer config、README、examples、tests 中统一。

当前建议采用模板定义作为唯一事实源：

- `01_摘要.md`
- `02_立项依据.md`
- `03_研究内容.md`
- `04_研究方案.md`
- `05_可行性分析.md`
- `06_创新点.md`
- `07_研究基础.md`

如果希望摘要最后写，也不应改变文件编号。执行顺序应由 `dependency_graph.priority` 控制，而不是通过文件名编号表达。

### P0-6：统一 `config.yaml`、`scores.yaml`、manifest 和 frontmatter 契约

需要把 Schema、默认配置、示例和 pipeline 文档对齐：

- `config.schema.yaml` 支持 `input_mode: auto`，或默认配置不再使用 `auto`。建议支持 `auto`，因为这是用户体验所需。
- `validate.py all` 应检查项目根目录的 `config.yaml`、`scores.yaml`，同时保留框架默认配置检查入口。
- `manifest.schema.yaml` 与 examples 统一为 `path/type/description/sections/key_content`。
- `outline.md` 和 `claim_registry.md` 示例补齐 frontmatter，或降低 Schema 对 frontmatter 的强制要求。建议保留 frontmatter，因为它有利于自动化。
- `scores.schema.yaml` 允许 `inner_scores` / `outer_scores` 使用结构化对象数组。

## P1 高优先级改进

### P1-1：修复测试在 Codex worktree 中不可运行的问题

当前测试硬编码了旧机器路径，导致 `pytest` 在 Codex worktree 中全失败。

需要修复：

- `tests/test_scripts.py` 的 `cwd='/Users/zedongyu/code/project/ScholarWriting'`
- `tests/test_validate.py` 中项目根目录多退了一层的问题
- 测试命令统一为 `uv run --with pytest --with pyyaml --with jsonschema pytest -q`

验收标准：

- 在任意 checkout/worktree 中运行测试不依赖绝对路径。
- 新增 Codex 适配测试，覆盖 plugin 结构、skill 元数据、agent 配置、示例校验。

### P1-2：补全 Python 依赖与 uv 项目管理

仓库规则要求 Python 项目使用 `uv`。当前只有 `scholar_writing/resources/scripts/requirements.txt`，且缺少 `jsonschema`。

建议新增：

- `pyproject.toml`
- `uv.lock`，如果项目希望锁定依赖
- 开发依赖：`pytest`
- 运行依赖：`pyyaml`、`jsonschema`

同时更新文档：

- 安装：`uv sync`
- 测试：`uv run pytest -q`
- 校验：`uv run python scholar_writing/resources/scripts/validate.py all examples/demo-nsfc-proposal`

### P1-3：修复 R7 格式审阅脚本接口

R7 要求对 `sections/` 运行格式与引文检查，但 `check_format.py` 和 `check_references.py` 只支持单文件。

建议：

- 让 `check_format.py` 支持目录输入，返回 `{file: result, _summary: ...}`。
- 让 `check_references.py` 支持目录输入，返回全局引文统计。
- 或新增 `check_sections.py` 统一调用所有检查。
- R7 skill 的 `allowed-tools` 或 Codex agent sandbox 配置应允许运行脚本。

### P1-4：补一套 Codex 使用文档

建议新增或更新：

- `docs/codex-getting-started.md`
- `docs/codex-architecture.md`
- README 增加“Codex App 安装与验证”章节

必须讲清楚：

- plugin 安装方式
- repo skill 开发方式
- 如何触发 `scholar-writing-codex`
- 如何开启/验证 subagents
- 自动循环如何开始、暂停、恢复
- 产物路径和人工介入方式

### P1-5：把 Claude Code 版文档降级为 legacy adapter

现有 `adapters/claude-code/skills/pipeline/SKILL.md` 可以保留，但应明确：

- 它是 Claude Code adapter。
- Codex 使用 `skills/scholar-writing/SKILL.md` 或 `.agents/skills/scholar-writing/SKILL.md`。
- 不要让 Codex 入口引用 Claude Code 的 `allowed-tools` 和 `Agent` 语义。

## P2 中长期增强

### P2-1：把 writer/reviewer 角色从技能文档拆成可组合 prompt 包

当前每个 `SKILL.md` 同时承担：

- 触发元数据
- 角色说明
- 输入输出契约
- 质量标准
- 示例
- 写入路径

这对 Claude Code 勉强可用，但对 Codex 多 agent 编排不够清晰。建议逐步拆成：

- `prompts/writers/*.md`
- `prompts/reviewers/*.md`
- `schemas/*.yaml`
- `agents/*.toml`
- `skills/*/SKILL.md` 只保留触发和编排说明

### P2-2：提供非交互批处理模式

长期可以新增：

- `uv run scholar-writing plan <project_dir>`
- `uv run scholar-writing next <project_dir>`
- `uv run scholar-writing status <project_dir>`
- `uv run scholar-writing package-agent-task <project_dir> --role R1 --section 02_立项依据`

这样 Codex 负责写作和判断，脚本负责把“下一步该干什么”说清楚。

### P2-3：建立端到端示例项目

当前 examples 更像静态样本，不是可运行 fixture。建议新增：

- `examples/codex-minimal-from-outline`
- `examples/codex-minimal-from-draft`
- `examples/codex-review-loop`

每个示例都应能通过：

- `validate.py all`
- 至少一轮 `writer -> R1/R2/R3 -> revision` 的模拟或 dry-run
- 文档中给出的 Codex 触发语句

## 建议的 Codex-native 架构

### 目录结构

建议目标结构如下：

```text
ScholarWriting/
├── .codex-plugin/
│   └── plugin.json
├── .codex/
│   ├── config.toml
│   └── agents/
│       ├── scholar-architect.toml
│       ├── scholar-writer.toml
│       ├── scholar-reviewer.toml
│       └── scholar-revision.toml
├── skills/
│   └── scholar-writing/
│       ├── SKILL.md
│       └── references/
├── scholar-writing/
│   ├── prompts/
│   ├── scripts/
│   ├── schemas/
│   ├── templates/
│   └── references/
├── examples/
├── tests/
└── docs/
```

### Codex 入口 skill 的职责边界

入口 skill 负责：

- 判断任务类型。
- 建立项目目录结构。
- 调用确定性脚本读取状态。
- 显式请求 Codex 使用 subagents。
- 汇总各 agent 输出。
- 根据评分与严重级别决定下一轮。

入口 skill 不负责：

- 在一个巨大 prompt 内手写完整状态机。
- 伪装 Claude Code `Agent` 工具。
- 让每个 reviewer 自行决定是否进入下一轮。

### 自动循环的建议状态机

建议状态如下：

- `init`
- `planning`
- `section_writing`
- `section_reviewing`
- `section_revising`
- `global_reviewing`
- `global_revising`
- `expert_simulation`
- `human_needed`
- `completed`

每个状态只允许有限转移，并由脚本校验：

- `section_writing -> section_reviewing`
- `section_reviewing -> section_revising | approved | human_needed`
- `section_revising -> section_reviewing`
- `global_reviewing -> global_revising | completed | human_needed`
- `global_revising -> section_reviewing | global_reviewing`

### 多智能体调用策略

建议 Codex 中的并行策略：

- Architect：单 agent，写入 `planning/`。
- Writer：按 dependency graph 串行或同 priority 并行；初期建议串行。
- R1/R2/R3：同一章节三路并行。
- Revision：单 agent，避免多人同时写同一章节。
- R4/R5/R7：全文级并行；R6 按影响章节条件触发。
- R8：收敛后并行 3-5 个专家视角，然后主 agent 汇总。

重要约束：

- reviewer agent 必须 read-only，不修改 `sections/`。
- revision agent 是唯一能按审阅意见修改章节正文的角色。
- 主 agent 维护状态，不把 `scores.yaml` 的最终解释权交给子 agent。

## 分阶段落地路线

### 阶段 1：让 Codex 能安装和发现

目标：

- 新增 plugin 壳。
- 新增 Codex 入口 skill。
- 文档写清安装方式。

验收：

- Codex 重启后能在技能列表看到 `scholar-writing-codex`。
- 用户输入“帮我写国自然申报书”能触发入口 skill。

### 阶段 2：让示例和校验自洽

目标：

- 修复配置、manifest、outline、claim_registry、scores Schema 漂移。
- 修复章节编号契约。
- 修复测试路径。
- 补齐依赖。

验收：

- `uv run pytest -q` 通过。
- `uv run python scholar_writing/resources/scripts/validate.py all examples/demo-nsfc-proposal --format json` 通过。
- 默认配置通过校验。

### 阶段 3：让一轮“写作-审查-修订”跑通

目标：

- 新增最小 loop controller。
- 支持 from_outline 示例。
- 主 agent 可显式并行触发 R1/R2/R3。
- Revision 后能回到 review。

验收：

- 对一个最小章节项目完成一轮 writer -> reviewers -> revision -> reviewers。
- `scores.yaml` 记录轮次、分数、状态转移。
- 审阅报告和修改记录路径稳定。

### 阶段 4：让全文外环和专家模拟跑通

目标：

- 实现 R4/R5/R7/R6 全文级审阅。
- 实现受影响章节检测。
- 实现 R8 专家模拟。

验收：

- 全文达到阈值后进入 `completed`。
- 未达到阈值时能识别受影响章节并回到内环。
- 超轮次时进入 `human_needed`，并输出具体人工介入说明。

## 最小可执行验收清单

在宣称“Codex 适配完成”之前，至少应满足：

- Codex 能发现入口 skill。
- Codex 能明确触发 subagents，而不是只在主会话里写完所有内容。
- `from_outline` 能完成至少一章的写作、R1/R2/R3 审阅和 Revision。
- `scores.yaml` 结构通过 Schema。
- 所有 examples 通过 `validate.py all`。
- `uv run pytest -q` 在 Codex worktree 中通过。
- README 同时包含 Claude Code 和 Codex 两套入口，且不会混用工具语义。

## 建议优先实现的文件变更

第一批：

- `.codex-plugin/plugin.json`
- `skills/scholar-writing/SKILL.md`
- `.codex/agents/scholar-architect.toml`
- `.codex/agents/scholar-writer.toml`
- `.codex/agents/scholar-reviewer.toml`
- `.codex/agents/scholar-revision.toml`
- `docs/codex-getting-started.md`
- `pyproject.toml`

第二批：

- `scholar_writing/resources/scripts/validate.py`
- `scholar_writing/resources/schemas/config.schema.yaml`
- `scholar_writing/resources/schemas/scores.schema.yaml`
- `scholar_writing/resources/schemas/manifest.schema.yaml`
- `scholar_writing/resources/templates/nsfc/base.yaml`
- `adapters/claude-code/skills/writer/nsfc/*/config.yaml`
- `examples/**`
- `tests/**`

第三批：

- `scholar_writing/resources/scripts/run_pipeline.py`
- `scholar_writing/resources/scripts/pipeline_state.py`
- `scholar_writing/resources/scripts/check_sections.py`
- `docs/codex-architecture.md`

## 风险判断

最大风险不是 Codex 不支持多智能体。Codex 支持 subagents 和 custom agents。真正的问题是当前仓库没有用 Codex 的发现、配置和调度方式表达这些角色。

第二个风险是过早把 18 个 agent 全部迁移成 Codex custom agents。这样会制造大量配置面，反而更难验证。建议先用 4 类 agents 跑通闭环，再逐步拆分 R1-R8。

第三个风险是继续把 pipeline 写成超长自然语言说明。自然语言适合描述策略，但自动循环需要稳定状态机和可测试脚本。写作质量可以交给 LLM，轮次、路径、评分聚合和停止条件应交给确定性代码。

