# 配置说明

ScholarWriting 通过 YAML 配置文件控制项目行为。配置分为两层：框架默认配置和项目级配置。

## 配置加载顺序

1. `scholar-writing/config/default_config.yaml` — 框架默认值
2. `<project>/config.yaml` — 项目级配置（覆盖默认值）

## 完整配置参数

### project 项目基本信息

```yaml
project:
  name: "项目名称"                    # 项目名称（仅供显示）
  type: nsfc                          # 项目类型：nsfc | paper
  template: 面上项目                   # 模板名称，对应 templates/ 下的文件
  input_mode: from_materials           # 入口模式：from_materials | from_outline | from_draft
  language: zh                         # 语言：zh | en
```

**input_mode 说明：**

| 模式 | 用户需提供 | 系统起始阶段 |
|------|-----------|------------|
| `from_materials` | `materials/` 目录 | Architect → Writer → Reviewer |
| `from_outline` | `planning/outline.md` | Writer → Reviewer |
| `from_draft` | `sections/*.md` | Reviewer → Revision |

### convergence 收敛控制

```yaml
convergence:
  section_score_threshold: 80          # 章节内环通过分 (0-100)
  global_score_threshold: 85           # 全文外环通过分 (0-100)
  max_major_issues: 2                  # 外环收敛条件：最大允许 major 问题数
  max_section_rounds: 3                # 章节内环最大迭代轮次
  max_global_rounds: 5                 # 全文外环最大迭代轮次
  human_intervention_on_timeout: true  # 超过最大轮次时是否请求人工介入
  full_consistency_check_interval: 2   # 每 N 轮外环强制一次全文一致性检查
```

**收敛条件（外环）：**
- 条件 A：`global_score >= global_score_threshold`
- 条件 B：本轮 `critical == 0` 且 `major <= max_major_issues`
- A 和 B 同时满足 → 完成
- 达到 `max_global_rounds` 但未满足 → 根据 `human_intervention_on_timeout` 决定行为

### score_weights 评分权重

```yaml
score_weights:
  section:                             # 章节级评分权重（内环，R1-R3）
    logic: 0.40                        #   逻辑审阅权重
    de_ai: 0.25                        #   去 AI 化审阅权重
    completeness: 0.35                 #   完备性审阅权重
  global:                              # 全文级评分权重（外环，R4-R7）
    consistency: 0.30                  #   一致性审阅权重
    narrative: 0.35                    #   叙事审阅权重
    feasibility: 0.20                  #   可行性审阅权重
    format: 0.15                       #   格式审阅权重
```

各组权重之和必须为 1.0。

### checklist_weight_map Checklist 条目权重

```yaml
checklist_weight_map:
  critical: 3                          # critical 级条目的权重系数
  high: 2                              # high 级条目的权重系数
  medium: 1                            # medium 级条目的权重系数
```

Reviewer 对每条 Checklist 条目打分（0-100），按此权重加权聚合为维度分：

```
维度分 = sum(条目分 * 条目权重) / sum(条目权重)
```

### critical_threshold 关键项阈值

```yaml
critical_threshold: 60                 # critical 条目低于此分数触发短路规则
```

任一 critical 级 Checklist 条目得分低于此阈值时，触发短路规则：该维度标红，章节/全文总分额外扣 10 分。

### dry_run 试运行

```yaml
dry_run: false                         # true: 只输出执行计划，不实际运行 Agent
```

启用后，Pipeline 会输出完整的执行计划（Agent 调用顺序、预估 token 消耗），但不实际调用任何 Agent。

## 项目目录结构

运行后，项目目录将包含以下结构：

```
project/
├── config.yaml                  # 项目配置
├── materials/                   # 用户输入材料 (from_materials 模式)
├── planning/                    # Architect 产出
│   ├── outline.md               #   全文大纲
│   ├── dependency_graph.yaml    #   章节依赖 DAG
│   ├── claim_registry.md        #   核心论点注册表
│   └── material_mapping.md      #   材料-章节映射
├── sections/                    # 各章节文本
│   ├── 01_摘要.md
│   ├── 02_立项依据.md
│   └── ...
├── reviews/                     # 审阅报告（按轮次）
│   ├── round_1/
│   └── round_2/
├── change_logs/                 # 修改记录
│   ├── round_1_changes.md
│   └── round_2_changes.md
├── output/                      # 最终输出
└── scores.yaml                  # 状态追踪（自动生成）
```

## 模板配置

模板文件定义章节结构、依赖图和审阅策略。支持继承：

```yaml
# templates/nsfc/面上项目.yaml
extends: nsfc/base               # 继承基础模板

length_management:
  total_pages: 20
  compression_strategy: "..."
  expansion_strategy: "..."
```

子模板覆盖父模板的同名字段，未覆盖字段继承父模板值。
