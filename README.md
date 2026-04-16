# ScholarWriting

多智能体学术写作框架 —— 从素材到成稿的迭代收敛引擎。

> **项目状态**：本项目处于早期阶段，核心架构和 Agent 定义已基本完成，但仍有许多可以改进和完善的地方。欢迎通过 [Issues](https://github.com/pkgunboat/ScholarWriting/issues) 和 [Discussions](https://github.com/pkgunboat/ScholarWriting/discussions) 参与讨论、提出建议或贡献代码。

ScholarWriting 通过协调 18 个专业化 AI Agent（架构师、写作者、审阅者、修订者），自动完成学术文档的组织、写作、多维度审阅和迭代优化。系统借鉴 CI/CD 思想，将学术写作建模为可量化收敛的迭代过程。

## 特性

- **多 Agent 协作**：7 个章节写作 Agent + 8 个专项审阅 Agent + 架构师 + 修订者，各司其职
- **双层迭代收敛**：内环（章节级写作-审阅-修订）+ 外环（全文一致性-叙事-格式验证）
- **影响分析驱动**：修订时精确定位受影响章节，增量重审而非全文重跑
- **量化质量门控**：Checklist 驱动的多维度评分，可配置收敛阈值
- **去 AI 痕迹**：专项 De-AI 审阅维度，内置中文学术写作 AI 痕迹模式库
- **断点恢复**：通过 `scores.yaml` 状态追踪，跨会话无缝继续
- **模板可扩展**：支持模板继承，可自定义项目类型和评审标准

## 平台兼容性

本项目当前基于 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 的 Skill/Agent 系统开箱即用，但**核心设计与平台无关**。

**Claude Code 特有的部分**仅限于薄薄的调度层：
- SKILL.md 的 YAML frontmatter（`allowed-tools`、触发词）
- Pipeline 中通过 `Agent` 工具调度 sub-agent 的方式

**平台无关的部分**占绝大多数：
- SKILL.md 的指令正文 — 本质是结构化 Prompt，任何 LLM 都能理解和执行
- 模板、Checklist、Schema — 纯 YAML/JSON 数据文件
- 工具脚本 — 纯 Python，不依赖任何 LLM SDK
- 写作参考资料、句式模板 — 纯文档
- 工作流设计（双层迭代、评分聚合、收敛判定）— 通用的架构模式

因此，本框架可以适配到其他支持 Agent 编排的平台（如 Codex CLI、Gemini CLI、Cursor Agent、自定义 Agent 框架等），适配时主要需要替换 Pipeline 的调度方式，核心 Prompt、模板和 Schema 均可直接复用。欢迎社区贡献其他平台的适配方案。

## 系统架构

```
                        ┌─────────────────────────┐
                        │     Pipeline 编排器       │
                        │   (主会话层平铺调度)       │
                        └────────┬────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
        ┌─────▼─────┐    ┌──────▼──────┐    ┌──────▼──────┐
        │  规划层     │    │   执行层     │    │   验证层     │
        │ Architect  │    │  7 Writers  │    │ 8 Reviewers │
        │            │    │  1 Reviser  │    │             │
        └─────┬─────┘    └──────┬──────┘    └──────┬──────┘
              │                  │                  │
              └──────────────────┴──────────────────┘
                                 │
                    文件系统通信 (sections/, reviews/)

内环 (章节级):
  Writer → R1(逻辑) + R2(去AI) + R3(完备性) → 评分 → Revision → 循环

外环 (全文级):
  R4(一致性) + R5(叙事) + R6(可行性) + R7(格式) → 评分 → Revision → 循环
```

## 快速开始

### 环境要求

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Python 3.8+
- PyYAML (`pip install pyyaml`)

### 安装

```bash
# 克隆仓库
git clone https://github.com/pkgunboat/ScholarWriting.git

# 安装 Python 依赖
pip install -r scholar-writing/scripts/requirements.txt
```

### 将 Skills 注册到 Claude Code

将 `scholar-writing/skills/` 目录注册为 Claude Code 的 Skill 搜索路径。具体方式请参考 [Claude Code Skills 文档](https://docs.anthropic.com/en/docs/claude-code)。

### 创建项目

```bash
mkdir my-nsfc-proposal && cd my-nsfc-proposal
```

创建 `config.yaml`：

```yaml
project:
  name: "我的面上项目申请"
  type: nsfc
  template: 面上项目
  input_mode: from_materials   # 或 from_outline / from_draft
  language: zh
```

### 三种输入模式

| 模式 | 用户提供 | 适用场景 |
|------|---------|---------|
| `from_materials` | `materials/` 目录（PDF、笔记等） | 从零开始，有研究素材 |
| `from_outline` | `planning/outline.md` | 已有写作大纲 |
| `from_draft` | `sections/*.md` 各章节初稿 | 已有初稿，需要评审优化 |

### 运行

在 Claude Code 中触发 pipeline：

```
> 写申报书
```

或直接调用 Skill：

```
> /scholar-pipeline
```

系统将自动执行完整的写作-审阅-修订流程。

## 项目结构

```
scholar-writing/
├── config/                    # 默认配置
│   └── default_config.yaml    #   收敛阈值、评分权重
├── skills/                    # Agent 定义 (SKILL.md)
│   ├── pipeline/              #   总调度器
│   ├── architect/             #   素材分析 + 大纲生成
│   ├── revision/              #   影响分析 + 定向修订
│   ├── writer/nsfc/           #   7 个章节写作 Agent
│   └── reviewer/              #   8 个评审 Agent (R1-R8)
├── templates/nsfc/            # NSFC 项目模板
│   ├── base.yaml              #   基础模板 (章节定义 + 依赖图)
│   ├── 面上项目.yaml           #   面上项目特化
│   ├── 联合基金.yaml           #   联合基金特化
│   └── checklists/            #   评审检查清单 (7章节 + 1全局)
├── schemas/                   # 数据校验 Schema
├── references/                # 写作参考资料
│   ├── STYLE_GUIDE_ZH.md      #   学术写作风格指南
│   ├── DEAI_PATTERNS_ZH.md    #   去 AI 痕迹模式库
│   ├── NSFC_GUIDE.md          #   NSFC 申请指南
│   └── patterns/              #   分章节句式模板
└── scripts/                   # 工具脚本
    ├── validate.py            #   Schema + 语义校验
    ├── count_words.py         #   字数统计
    ├── check_format.py        #   格式检查
    ├── check_references.py    #   参考文献校验
    ├── check_cross_refs.py    #   跨章节引用分析
    └── export_docx.py         #   DOCX 导出
```

## 工作流程

### Phase 1: 规划 (Architect)

Architect Agent 分析用户素材，生成：
- `planning/outline.md` — 全文大纲（含各章核心论点）
- `planning/dependency_graph.yaml` — 章节依赖 DAG
- `planning/claim_registry.md` — 核心论点注册表（一致性锚点）

### Phase 2: 内环迭代 (章节级)

按依赖图拓扑顺序逐章处理：

1. **写作**：对应 Writer Agent 生成章节初稿
2. **评审**：R1(逻辑) + R2(去AI) + R3(完备性) 并行评审
3. **评分**：加权聚合 → `logic×0.40 + de_ai×0.25 + completeness×0.35`
4. **判定**：分数 ≥ 80 → 通过；否则 → 修订后重审（最多 3 轮）

### Phase 3: 外环迭代 (全文级)

所有章节通过后：

1. **全文评审**：R4(一致性) + R5(叙事) + R6(可行性) + R7(格式)
2. **评分**：`consistency×0.30 + narrative×0.35 + feasibility×0.20 + format×0.15`
3. **判定**：总分 ≥ 85 且无 critical 问题 → 完成；否则 → 修订受影响章节（最多 5 轮）

### Phase 4: 输出

最终校验通过后，导出 DOCX 文档。

## 配置说明

`config.yaml` 中的关键参数：

```yaml
convergence:
  section_score_threshold: 80    # 章节通过分
  global_score_threshold: 85     # 全文通过分
  max_section_rounds: 3          # 章节最大迭代轮次
  max_global_rounds: 5           # 全文最大迭代轮次

score_weights:
  section:
    logic: 0.40
    de_ai: 0.25
    completeness: 0.35
  global:
    consistency: 0.30
    narrative: 0.35
    feasibility: 0.20
    format: 0.15
```

完整配置说明请参考 [docs/configuration.md](docs/configuration.md)。

## 扩展开发

系统支持通过模板继承机制扩展到其他学术文档类型：

1. **新增项目模板**：在 `templates/` 下创建新模板 YAML，可继承 `base.yaml`
2. **新增 Writer Agent**：在 `skills/writer/` 下添加新的 SKILL.md
3. **新增 Reviewer**：在 `skills/reviewer/` 下添加新的审阅维度
4. **自定义 Checklist**：在 `templates/checklists/` 下定义新的评审标准

详细开发指南请参考 [docs/extending.md](docs/extending.md)。

## 设计理念

- **写作与编码的类比**：借鉴 CI/CD 思想，每次修改触发增量检查而非全文重跑
- **写作者与审阅者隔离**：Writer 和 Reviewer 在独立上下文中运行，避免自我修正偏差
- **审阅两步法**：先自由分析（充分推理），再对照 Checklist 结构化打分
- **清晰任务描述优于角色扮演**：Agent 依赖清晰的任务描述 + 细粒度 Checklist，而非 persona
- **Checklist 正面指令表述**：说"引文总数 ≥ 25 篇"而非"不要遗漏引文"

## 已知局限与待完善

本项目仍处于早期探索阶段，以下方面尚不完善：

- **论文写作支持**：当前仅实现了 NSFC 申报书模板，AI 顶会论文（NeurIPS/ICML/CVPR 等）的模板和 Writer Agent 尚未开发
- **R8 专家模拟**：Expert Simulation Reviewer 的 SKILL.md 已创建但功能尚未完善
- **端到端测试**：缺少对完整 Pipeline 流程的自动化集成测试
- **多平台适配**：当前仅在 Claude Code 上验证，其他平台的适配方案待社区贡献
- **评分体系调优**：默认的评分权重和收敛阈值基于有限的实践经验，可能需要根据具体场景调整

欢迎通过 [Issues](https://github.com/pkgunboat/ScholarWriting/issues) 反馈问题，通过 [Discussions](https://github.com/pkgunboat/ScholarWriting/discussions) 讨论设计方案，或直接提交 PR 参与贡献。

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。

## 致谢

本项目基于 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 的 Skill/Agent 系统构建。
