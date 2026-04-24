# ScholarWriting

ScholarWriting 是一个面向学术写作的多 agent 工作流框架。推荐先把它安装到本机 Codex，然后在你自己的写作项目里用自然语言启动，让 agent 按“规划、写作、审阅、修订、再审阅”的流程推进学术文档。

适用场景：

- 国自然申报书。
- 论文初稿。
- 已有材料的结构化成稿。
- 已有初稿的多维度审阅和优化。

普通用户的推荐入口：

1. 在 Codex 里让它根据仓库地址安装 ScholarWriting。
2. 在任意位置创建自己的写作项目。
3. 用 Codex 打开这个写作项目。
4. 在 Codex 里调用 `scholar-writing`。

示例：

```text
使用 scholar-writing 帮我写一个国自然面上项目申报书。
材料在 ./my-proposal/materials。
```

或：

```text
使用 scholar-writing 审阅并优化 ./my-proposal 里的申报书初稿。
```

agent 会读取项目文件，判断下一步该规划、写作、审阅还是修订。底层 CLI 是给 agent 和开发者用的状态推进工具，普通用户不需要把它当作主要入口。

框架会自动加载写作规则资料。`scholar-writing/references/` 中的风格指南、国自然结构规范、去 AI 痕迹规则和章节句式模板会进入任务包，Codex 或 Claude Code agent 按这些规则写作、审阅和修订。用户只需要提供自己的材料、提纲或初稿。

## 安装到本机 Codex

在 Codex 里说：

```text
帮我安装这个仓库：https://github.com/<owner>/<repo>
```

如果仓库已经在本机，也可以说：

```text
帮我安装本机这个仓库：./ScholarWriting
```

Codex 应读取仓库根目录的 `SKILL.md`，然后执行安装流程。安装完成后，重启 Codex，让 Codex 重新发现 `scholar-writing` skill 和 custom agents。

如果你在终端里手动安装，可以在本仓库根目录执行：


```bash
bash scripts/install-codex.sh
```

如果检测到旧版 `scholar-writing` 安装，安装流程会停止。用户确认覆盖后，Codex 或终端再执行：

```bash
bash scripts/install-codex.sh --replace
```

安装脚本会写入：

```text
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/
${CODEX_HOME:-$HOME/.codex}/agents/scholar-*.toml
```

安装内容包括：

- Codex 全局 skill：`scholar-writing`
- 4 个 Codex custom agents：architect、writer、reviewer、revision
- ScholarWriting runtime：Python controller、schemas、templates、references、prompts
- 包装命令：`bin/scholar-writing`

安装后重启 Codex，让 Codex 重新发现 skill 和 agents。

## 从本机 Codex 删除

在 Codex 里说：

```text
帮我卸载 scholar writing
```

或者：

```text
帮我卸载本机这个仓库：./ScholarWriting
```

Codex 应按仓库根目录 `SKILL.md` 中的卸载流程清理本机安装。

如果你在终端里手动卸载，可以在本仓库根目录执行：

```bash
bash scripts/uninstall-codex.sh
```

卸载脚本会删除安装到 Codex 的 skill runtime 和 `scholar-*` agents。它不会删除你的写作项目目录，也不会删除你已经生成的申报书材料。

## 在自己的写作项目中使用 Codex

安装完成后，日常使用发生在你自己的项目目录里。

### 1. 新建写作项目

你可以让 Codex 创建项目骨架：

```text
使用 scholar-writing 创建一个国自然面上项目写作目录，目录名是 my-proposal。
```

也可以自己建目录后放入材料：

```text
my-proposal/
├── materials/
├── planning/
├── sections/
├── reviews/
└── revisions/
```

### 2. 放入你的材料或初稿

把已有内容放到项目目录：

| 你已有的内容 | 建议放置位置 |
| --- | --- |
| 文献、笔记、实验结果、前期基础 | `my-proposal/materials/` |
| 素材清单 | `my-proposal/materials/manifest.yaml` |
| 已有提纲 | `my-proposal/planning/outline.md` |
| 已有章节初稿 | `my-proposal/sections/*.md` |

然后告诉 Codex：

```text
使用 scholar-writing 继续处理 ./my-proposal。
```

### 3. 让 Codex 进入写作流程

从素材开始：

```text
使用 scholar-writing 基于 ./my-proposal/materials 生成申报书大纲，并继续写作。
```

从提纲开始：

```text
使用 scholar-writing 根据 ./my-proposal/planning/outline.md 开始逐章写作。
```

从初稿开始：

```text
使用 scholar-writing 审阅并优化 ./my-proposal/sections 里的初稿。
```

你也可以直接描述当前情况：

```text
我已经有一版国自然初稿，章节文件在 ./my-proposal/sections。
使用 scholar-writing 做多维度审阅，必要时自动修订；遇到核心论点或大结构调整时先问我。
```

### 4. Codex 会自动做什么

Codex 的 ScholarWriting skill 会按以下顺序工作：

1. 识别项目目录。
2. 读取项目配置、素材、提纲、初稿和状态文件。
3. 计算下一步动作。
4. 生成当前任务包。
5. 根据任务包中的 `reference_inputs` 读取必要写作规则。
6. 调用合适的 Codex custom agent。
7. 把审阅或修订结果写回项目状态。
8. 再次判断是否需要继续写作、继续审阅、继续修订或停止。

当前 Codex 适配层包含 4 类角色：

| Codex 角色 | 负责内容 |
| --- | --- |
| `scholar-architect` | 分析素材，生成大纲、论点注册表和章节依赖 |
| `scholar-writer` | 根据任务包写作或补全章节 |
| `scholar-reviewer` | 按指定维度审阅章节或全文 |
| `scholar-revision` | 根据审阅意见做定向修订 |

安装后的 Codex skill 会使用安装目录里的 runtime 和 references。你的写作项目只保存自己的材料、提纲、章节、审阅和修订结果。

### 5. 什么时候会暂停问你

普通文字优化、局部补充、轻中度结构调整可以自动推进。

遇到这些情况时，Codex 应该暂停并询问你：

- 需要改变核心论点。
- 需要大幅调整章节结构。
- 关键事实、数据或引用不确定。
- 审阅发现 critical 问题。
- 修改会明显影响多个章节的一致性。

## 在 Claude Code 中使用

Claude Code 使用本仓库的 Claude Code 适配层：

```text
scholar-writing/skills/pipeline/
scholar-writing/skills/architect/
scholar-writing/skills/writer/nsfc/
scholar-writing/skills/reviewer/
scholar-writing/skills/revision/
```

使用方式同样应以自然语言为主：

```text
使用 scholar-writing 帮我基于 ./my-proposal/materials 写一份国自然申报书。
```

或：

```text
使用 scholar-writing 审阅优化 ./my-proposal 的已有初稿。
```

Claude Code 适配层的角色拆分更细，包含章节 writer、专项 reviewer、修订 agent 和专家模拟 reviewer。它适合沿用 Claude Code 的 agent 调度语义。

如果你同时使用 Codex 和 Claude Code，需要记住：

| 项目 | Codex | Claude Code |
| --- | --- | --- |
| 用户入口 | 自然语言触发 `scholar-writing` skill | 自然语言触发 `scholar-writing` skill |
| agent 粒度 | 4 类通用角色 | 更细的章节与审阅角色 |
| 状态推进 | 依赖共享 Python controller 和 `scores.yaml` | 读取同一类项目文件，使用 Claude Code 适配层执行 |
| 推荐使用场景 | 当前主要开发和验证路径 | 保留 Claude Code 工作流与细粒度角色能力 |

## 写作项目长什么样

一个典型项目目录：

```text
my-proposal/
├── config.yaml
├── scores.yaml
├── materials/
│   └── manifest.yaml
├── planning/
│   ├── outline.md
│   ├── claim_registry.md
│   └── dependency_graph.yaml
├── sections/
│   ├── 01_摘要.md
│   ├── 02_立项依据.md
│   ├── 03_研究内容.md
│   ├── 04_研究方案.md
│   ├── 05_可行性分析.md
│   ├── 06_创新点.md
│   └── 07_研究基础.md
├── reviews/
└── revisions/
```

不要求你一开始就准备完整目录。你可以只有素材、只有大纲，或者只有初稿。agent 会根据已有文件判断入口。

## 自动优化循环

ScholarWriting 的循环会把生成任务和状态判断分开，避免 agent 凭感觉反复改：

| 层次 | 职责 |
| --- | --- |
| Agent | 写作、审阅、修订 |
| Python controller | 判断下一步、记录状态、聚合评分、决定是否暂停 |

典型流程：

```text
已有初稿
  -> 审阅
  -> 生成审阅结果
  -> 判断是否达标
  -> 未达标则修订
  -> 再审阅
  -> 达标后停止
```

核心状态写在 `scores.yaml`。它记录当前阶段、下一步动作、章节状态、最近审阅分数、是否需要用户确认等信息。

普通用户不需要手动编辑 `scores.yaml`。如果流程中断，下次继续让 agent 处理同一个项目目录即可。

每次生成任务包时，controller 也会选择对应 references：

- 写作任务会加载中文学术风格、通用句式、国自然结构和分章节模板。
- 审阅任务会按维度加载结构、完备性、格式或 de-AI 规则。
- 修订任务会结合审阅结果和同一组规则，输出可追踪的修改依据。

## 支持的输入方式

ScholarWriting 会根据项目中已有文件自动判断从哪里开始：

| 已有文件 | 入口模式 | 下一步 |
| --- | --- | --- |
| `materials/` | 从素材开始 | 规划和生成大纲 |
| `planning/outline.md` | 从提纲开始 | 章节写作 |
| `sections/*.md` | 从初稿开始 | 审阅和修订 |

如果内容不足，agent 会向你追问。

## 当前能力边界

当前已经具备：

- Codex skill 入口。
- Codex 4 类 custom agents。
- Claude Code 适配层。
- 项目状态文件和自动恢复机制。
- references 自动接入 taskpack，写作、审阅和修订会读取质量规则。
- 从素材、提纲、初稿三种入口开始。
- 写作、审阅、修订的基础闭环。
- 国自然项目的章节结构和命名契约。

当前仍在建设：

- Codex plugin 级别的一键分发。
- 更细粒度的 Codex agent 拆分。
- 真实 LLM API 封装。
- 完整 DOCX/PDF 导出链路。
- 更完整的论文模板。

## 给开发者：命令行和验证

下面这些命令主要用于调试、验证和开发，普通用户通常不需要手动执行。

### 源码仓库内调试

开发者可以直接在本仓库里调试 repo-local skill 和 agents：

```text
.agents/skills/scholar-writing/SKILL.md
.codex/agents/scholar-architect.toml
.codex/agents/scholar-writer.toml
.codex/agents/scholar-reviewer.toml
.codex/agents/scholar-revision.toml
```

在源码仓库调试时，可以直接要求：

```text
使用 scholar-writing 审阅优化 examples/from-draft。
```

这条路径用于开发和验证 skill/agent 文案、taskpack 契约、references 接入和状态机行为。普通用户的日常写作仍建议使用本机安装后的 workflow。

安装依赖：

```bash
uv sync
```

安装到本机 Codex：

```bash
bash scripts/install-codex.sh
```

卸载本机 Codex 安装：

```bash
bash scripts/uninstall-codex.sh
```

运行测试：

```bash
uv run pytest -q
```

开发 smoke：

```bash
uv run scholar-writing next examples/from-materials --format json
uv run scholar-writing next examples/from-outline --format json
uv run scholar-writing next examples/from-draft --format json
uv run scholar-writing taskpack examples/from-draft --format json
```

预期：

| 示例 | 下一步 |
| --- | --- |
| `examples/from-materials` | `run_architect` |
| `examples/from-outline` | `run_writer` |
| `examples/from-draft` | `run_reviewers` |

### 安装器调试

调试一键安装时，不要直接污染真实 Codex Home。使用临时目录：

```bash
CODEX_HOME=.codex-dev-home bash scripts/install-codex.sh --no-sync
CODEX_HOME=.codex-dev-home .codex-dev-home/skills/scholar-writing/bin/scholar-writing --help
CODEX_HOME=.codex-dev-home bash scripts/uninstall-codex.sh
```

`.codex-dev-home` 是本地临时调试目录，不应提交。

创建项目骨架：

```bash
uv run scholar-writing init my-proposal --type nsfc --mode auto
```

查看下一步：

```bash
uv run scholar-writing next my-proposal --format json
```

生成 agent 任务包：

```bash
uv run scholar-writing taskpack my-proposal --format json
```

任务包中的 `reference_inputs` 会列出本轮 agent 应读取的质量规则文件。新增规则资料时，开发者应维护 `scholar-writing/config/reference_registry.yaml`，并确保路径仍为相对路径。

写回审阅或修订事件：

```bash
uv run scholar-writing advance my-proposal --event-file review-result.yaml --format json
```

## 给开发者：框架历史和实现差异

本项目最早围绕 Claude Code 的 Skill/Agent 方式设计，因此仓库里保留了较细的角色资产，包括 architect、多个 NSFC writer、多个 reviewer、revision 和 expert simulation。

Codex 适配先建立共享的项目文件契约、状态机、CLI、schema 和 taskpack，再用 Codex 的 skill/custom agent 机制执行任务。

因此当前实现是：

- 共享核心：`scholar_writing/`、schemas、templates、reference registry、项目目录结构、`scores.yaml`。
- Codex 适配：`.agents/skills/scholar-writing/` 和 `.codex/agents/`。
- Claude Code 适配：`scholar-writing/skills/` 下的角色资产。

这也是为什么两个框架的 agent 数量、调度方式和并行方式不同，但可以处理同一类写作项目。

## 项目目录

```text
.
├── .agents/skills/scholar-writing/
│   └── SKILL.md
├── .codex/agents/
│   ├── scholar-architect.toml
│   ├── scholar-writer.toml
│   ├── scholar-reviewer.toml
│   └── scholar-revision.toml
├── scholar_writing/
│   ├── cli.py
│   ├── core/
│   └── prompts/
├── scholar-writing/
│   ├── schemas/
│   ├── scripts/
│   ├── skills/
│   └── templates/
├── docs/
├── examples/
└── tests/
```

## 更多文档

- [Codex 使用指南](docs/codex-getting-started.md)
- [Codex 架构说明](docs/codex-architecture.md)
- [Codex 适配审查](docs/codex-adaptation-review.md)
- [Codex 适配 QA 记录](docs/codex-adaptation-qa.md)
- [References 接入改造方案](docs/reference-integration-redesign.md)
- [Schema 说明](scholar-writing/schemas/README.md)

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。
