# 快速上手

本文档帮助你快速开始使用 ScholarWriting。

## 前提条件

1. **Claude Code CLI**：已安装并配置好 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
2. **Python 3.8+**：用于运行辅助脚本
3. **PyYAML**：`pip install pyyaml`

## 安装

```bash
git clone https://github.com/pkgunboat/ScholarWriting.git
cd ScholarWriting
pip install -r scholar-writing/scripts/requirements.txt
```

将 `scholar-writing/skills/` 注册为 Claude Code 的 Skill 搜索路径。

## 创建第一个项目

### 方式一：从素材开始 (from_materials)

适合已有研究积累，希望从零开始生成申报书的场景。

```bash
mkdir my-proposal && cd my-proposal
```

1. 准备素材目录：

```bash
mkdir -p materials
# 将你的前期论文、研究笔记、实验数据放入 materials/
```

2. 创建 `config.yaml`：

```yaml
project:
  name: "基于多模态大模型的智能交互研究"
  type: nsfc
  template: 面上项目
  input_mode: from_materials
  language: zh
```

3. 在 Claude Code 中启动：

```
> 写申报书
```

系统将自动：Architect 分析素材 → 生成大纲（需你确认）→ 逐章写作 → 多维度审阅 → 迭代修订 → 输出成稿。

### 方式二：从大纲开始 (from_outline)

适合已有明确写作思路的场景。

1. 创建 `planning/outline.md`：

```markdown
# 项目大纲

## 立项依据
- 核心论点：当前 XX 领域存在 YY 问题
- 研究空白：现有方法在 ZZ 方面不足
- 科学问题：如何实现 ...

## 研究内容
- 研究目标 1：...
- 研究目标 2：...

## 研究方案
- 技术路线：...

...
```

2. 设置 `config.yaml` 中 `input_mode: from_outline`

### 方式三：从初稿开始 (from_draft)

适合已有初稿，希望通过系统评审优化的场景。

1. 将各章节初稿放入 `sections/` 目录：

```
sections/
├── 01_摘要.md
├── 02_立项依据.md
├── 03_研究内容.md
├── 04_研究方案.md
├── 05_可行性分析.md
├── 06_创新点.md
└── 07_研究基础.md
```

2. 设置 `config.yaml` 中 `input_mode: from_draft`

系统将跳过写作阶段，直接进入审阅-修订循环。

## 监控进度

运行过程中，系统会实时输出：
- 当前阶段和章节
- 各维度评分
- 修订建议摘要

`scores.yaml` 记录完整状态，支持断点恢复。如果中途中断，重新启动时系统会自动从上次位置继续。

## 人工介入

当章节或全文分数无法在最大轮次内达到阈值时，系统标记 `needs_human` 并暂停。此时你可以：

1. 手动编辑对应章节文件
2. 重新启动 Pipeline，系统会从修改后的状态继续

## 调整参数

如果迭代轮次过多或评审过严/过松，可以调整 `config.yaml`：

```yaml
convergence:
  section_score_threshold: 75    # 降低章节通过分
  global_score_threshold: 80     # 降低全文通过分
  max_section_rounds: 2          # 减少章节迭代轮次
```

## 试运行

在正式运行前，可以预览执行计划：

```yaml
dry_run: true
```

系统会输出 Agent 调用顺序和预估 token 消耗，但不实际运行。

## 下一步

- [配置说明](configuration.md) — 完整配置参数详解
- [系统架构](architecture.md) — 深入了解系统设计
- [扩展开发](extending.md) — 添加新模板和 Agent
