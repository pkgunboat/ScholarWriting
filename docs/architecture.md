# 系统架构

本文档详细说明 ScholarWriting 的系统架构设计。

## 设计理念

### 写作与编码的类比

传统学术写作是线性过程：起草 → 修改 → 定稿。ScholarWriting 借鉴 CI/CD 思想，将写作建模为迭代收敛过程：每次修改触发增量检查，精确定位影响范围，只重审受影响章节。

### 核心设计原则

1. **清晰任务描述优于角色扮演**：Agent 不依赖 persona 提升质量，而是依赖清晰的任务描述 + 细粒度 Checklist
2. **写作者与审阅者隔离上下文**：Writer 和 Reviewer 在独立上下文中运行，避免自我修正偏差
3. **审阅两步法**：先自由分析（充分推理），再对照 Checklist 结构化打分
4. **章节级拆分粒度**：复杂任务要拆分但不过度拆分，不需要细到段落级
5. **Checklist 正面指令表述**：说"引文总数 ≥ 25 篇"而非"不要遗漏引文"

## Agent 角色体系

系统由 6 类核心 Agent 组成，分为三层。

### 规划层

**Architect Agent（架构师）**

接收用户输入材料，分析提取论点，构建文档骨架。

输入：`materials/` 目录下的所有材料 + `config.yaml`

产出物：
- `outline.md` — 全文大纲，每个章节的核心论点和预期篇幅
- `dependency_graph.yaml` — 章节间的依赖关系 DAG
- `claim_registry.md` — 核心论点注册表，记录同一论点在各章节中的表述方式
- `material_mapping.md` — 材料到章节的映射关系

### 执行层

**Section Writer Agents（章节写作者）**

按章节类型拆分为独立 Writer Agent，每个 Writer 内嵌该章节特有的写作策略：

| Writer | 核心写作策略 |
|--------|------------|
| 摘要 | 全文压缩，关键词前置，目的/方法/预期成果三段式 |
| 立项依据 | 文献综述 → 研究空白 → 科学问题的逻辑递进 |
| 研究内容 | 结构化研究目标，与立项依据中识别的空白一一对应 |
| 研究方案 | 具体方法描述 + 技术路线图 + 年度时间表 |
| 可行性分析 | 条件论证 + 团队能力 + 风险预案 |
| 创新点 | 差异化提炼，措辞精准，避免空洞 |
| 研究基础 | 前期成果梳理，与研究方案形成支撑关系 |

**Revision Agent（修订者）**

根据审阅意见对指定章节进行定向修改，核心能力是影响分析：精确标注哪些其他章节可能受修改波及。

### 验证层

将审阅拆分为 8 个专项 Reviewer，分章节级和全文级两组。

**章节级 Reviewer（内环）：**
- **R1 Logic**：论证链完整性、前提是否成立、循环论证检测
- **R2 De-AI**：检测 AI 生成痕迹，包括公式化开头、空洞断言、模板化过渡
- **R3 Completeness**：对照 Checklist 验证必要元素是否存在

**全文级 Reviewer（外环）：**
- **R4 Consistency**：术语一致性、论点一致性、数据一致性
- **R5 Narrative**：全文叙事弧线、章节过渡自然度
- **R6 Feasibility**：研究方案可执行性、时间规划合理性
- **R7 Format**：篇幅比例、页数限制、标题层级、引文格式
- **R8 Expert Simulation**：模拟评审专家视角（计划中）

## 双层迭代收敛引擎

### 内环：章节写作-审阅循环

按 `dependency_graph.yaml` 的拓扑顺序逐章处理：

```
Writer 写作 → R1+R2+R3 并行审阅 → 加权评分
    ↓                                    ↓
  ≥ 80 分 → 通过              < 80 分 → Revision → 重新审阅
                                         (最多 3 轮)
```

章节级评分聚合：
```
section_score = logic × 0.40 + de_ai × 0.25 + completeness × 0.35
```

### 外环：全文验证-修改循环

所有章节通过后进入外环：

```
R4+R5+R7 并行审阅 (+ R6 条件触发) → 加权评分
    ↓                                        ↓
  ≥ 85 分且无 critical → 完成    < 85 分 → Revision → 受影响章节重入内环
                                              (最多 5 轮)
```

全文级评分聚合：
```
global_score = consistency × 0.30 + narrative × 0.35
             + feasibility × 0.20 + format × 0.15
```

### 收敛判定

外环收敛需要同时满足：
- 条件 A：加权总分 ≥ `global_score_threshold`
- 条件 B：本轮 critical = 0 且 major ≤ `max_major_issues`

超过最大轮次仍未收敛 → 暂停，请求人工介入。

## 上下文预算管理

为防止 Agent 上下文溢出，采用分层压缩策略：

| Agent 类型 | 输入内容 | 预算控制 |
|-----------|---------|---------|
| Section Writer | 大纲 + checklist + 前序章节 + 素材 | 前序章节只传递摘要（200-300 字） |
| Section Reviewer | 章节文本 + checklist | 单章节 + 对应 checklist |
| Revision Agent | 原文 + 审阅报告 + claim_registry | 只传递当前章节的审阅报告 |
| Global Reviewer | 全文 + checklist | 每章压缩为 500 字摘要 + 重点章节原文 |

## Agent 间通信

所有 Agent 通过文件系统通信，不共享上下文窗口。编排器（Pipeline）运行在主会话层，通过 `Agent` 工具平铺调用各 Writer/Reviewer Agent。

状态通过 `scores.yaml` 管理，支持断点恢复。

## 脚本与 LLM 职责划分

| 任务 | 执行方式 | 理由 |
|------|---------|------|
| 字数统计、篇幅比例 | `count_words.py` | 确定性计算 |
| 引文格式检查 | `check_references.py` | 正则匹配 |
| 章节结构验证 | `check_format.py` | 标题层级、编号规范 |
| 跨章节引用检测 | `check_cross_refs.py` | 引用级自动标记 |
| 导出 Word | `export_docx.py` | pandoc 转换 |
| 逻辑审阅、去 AI 化、叙事评价 | LLM Agent | 需要语义理解 |
| 一致性检查 | 混合 | 术语匹配用脚本预筛，语义一致性用 LLM |

## 错误处理

| 故障场景 | 恢复策略 |
|---------|---------|
| Writer 产出空内容或格式错误 | 重新调用 Writer，最多重试 2 次；仍失败则标记 `needs_human` |
| Reviewer 返回无法解析的评分 | 重新调用 Reviewer，最多重试 2 次；仍失败则沿用上一轮分数 |
| 脚本执行失败 | 记录错误日志，跳过该检查项，不阻塞流程 |
| 外环分数持续不收敛 | 连续 2 轮总分变化 < 2 分且未达阈值 → 标记 `needs_human` |
| 上下文窗口溢出 | 启用更激进的摘要策略，重试 |
