---
name: scholar-pipeline
description: |
  学术写作全流程编排器。自动协调规划、写作、审阅的多轮迭代。
  触发词：写申报书、写论文、学术写作、开始写作、write proposal、
  write paper、nsfc、国自然
  适用：国自然申报书、AI顶会论文等学术文档的端到端生成与迭代优化。
allowed-tools: [Read, Write, Edit, Bash, Agent]
---

# Scholar Pipeline — 学术写作全流程编排器

> Legacy adapter note: this file is the Claude Code adapter for the original
> pipeline and intentionally uses Claude Code concepts such as `allowed-tools`
> and `Agent(...)` style delegation. Codex should not use this file as its
> workflow entrypoint. For Codex, use `.agents/skills/scholar-writing/SKILL.md`
> and the deterministic CLI: `uv run scholar-writing next <project_dir>`.

> Shared core note: new platform-neutral behavior belongs in `scholar_writing/`
> and repository schemas/tests. Keep this legacy adapter aligned with the
> shared core instead of adding new state-machine logic here.

## Section 0: 交互式项目初始化

当用户触发 Pipeline 时（如输入"写申报书"、"帮我写国自然"等），首先检查项目状态，
根据当前目录的内容自动创建配置或引导用户补充材料。

```
交互式初始化流程：

0.1 检查 config.yaml 是否存在
    if config.yaml 不存在:
        # 新项目：通过对话引导用户创建
        → 执行 Section 0.2（交互式项目创建）
    else:
        # 已有项目：跳到 Section 1 正常初始化
        → 跳转 Section 1

0.2 交互式项目创建
    询问用户（可从用户的触发消息中提取信息，减少交互轮次）：

    Q1: "请问项目名称是什么？（如：基于多模态感知的智能人机交互关键技术研究）"
    Q2: "项目类型？（默认：nsfc）"
        → project_type
    Q3: "申报模板？（面上项目 / 青年基金 / 联合基金，默认：面上项目）"
        → project_template

    # 根据回答生成 config.yaml
    Write("config.yaml", {
        project:
          name: {用户回答}
          type: {project_type}
          template: {project_template}
          input_mode: auto
          language: zh
    })

    输出："已创建 config.yaml"

0.3 检测已有输入材料
    detected_inputs = []
    if sections/ 下存在 .md 文件:
        detected_inputs.append("sections/*.md（章节初稿）")
    if planning/outline.md 存在:
        detected_inputs.append("planning/outline.md（写作大纲）")
    if materials/ 下存在文件:
        detected_inputs.append("materials/（研究素材）")

    if detected_inputs 不为空:
        输出："检测到以下已有材料："
        for item in detected_inputs:
            输出："  - {item}"
        输出："将基于这些材料启动 Pipeline。"
        → 跳转 Section 1

0.4 无任何输入材料 — 引导用户选择模式
    输出：
    "当前项目目录为空，请选择一种启动方式：

     **方式 A：从素材开始**（推荐，适合有前期积累的场景）
     请将研究素材（论文 PDF、笔记、实验数据等）放入 materials/ 目录。
     我会分析素材并自动生成写作大纲。

     **方式 B：从大纲开始**（适合已有明确写作思路的场景）
     请提供各章节的核心论点和预期内容，我会创建 planning/outline.md。
     你也可以直接在对话中描述你的研究思路，我来帮你整理大纲。

     **方式 C：从初稿开始**（适合已有初稿需要优化的场景）
     请将各章节初稿放入 sections/ 目录（命名：01_摘要.md、02_立项依据.md 等）。
     我会直接进入多维度审阅和优化。

     请选择（A/B/C），或直接描述你的情况，我会推荐合适的方式。"

    等待用户回复 → 根据回复：

    case 用户选择 A 或描述有素材:
        Bash("mkdir -p materials")
        提示用户将素材放入 materials/ 目录
        if 用户在对话中直接提供了文本内容:
            将内容保存到 materials/ 下对应文件
        提示用户提供 materials/manifest.yaml 或帮助生成：
            "请简要描述每份素材的内容和它与申报书哪些章节相关，
             我来帮你生成 manifest.yaml。"
        → 用户确认素材就绪后，跳转 Section 1

    case 用户选择 B 或描述了研究思路:
        Bash("mkdir -p planning")
        if 用户在对话中描述了研究内容:
            根据用户描述生成 planning/outline.md
            输出大纲内容，请用户确认或修改
        else:
            引导用户逐步描述：
            "请告诉我：
             1. 你的研究领域和方向
             2. 想解决什么问题
             3. 大致的技术路线或方法
             4. 前期有哪些相关积累"
            根据回答生成 planning/outline.md
        → 用户确认大纲后，跳转 Section 1

    case 用户选择 C 或提供了初稿文件:
        Bash("mkdir -p sections")
        提示用户将初稿放入 sections/ 目录
        if 用户在对话中直接粘贴了文本:
            按章节拆分并保存到 sections/ 下
        → 确认初稿就绪后，跳转 Section 1
```

## Section 1: 初始化

### 1.1 读取配置

Pipeline 启动时，加载项目配置和模板定义，构建完整的运行参数。

```
初始化流程：

1. 读取 config.yaml
   config = Read("config.yaml")
   project_type     = config.project.type          # 例如 "nsfc", "paper"
   project_template = config.project.template       # 例如 "youth_fund", "icml"
   input_mode       = config.project.input_mode     # "auto" | "from_materials" | "from_outline" | "from_draft"

   # 自动检测输入模式
   if input_mode == "auto" or input_mode 未设置:
       input_mode = detect_input_mode()
       输出："[自动检测] 输入模式: {input_mode}"

   detect_input_mode():
       # 优先级: from_draft > from_outline > from_materials
       # 检测到更高级产物时，跳过上游阶段
       if sections/ 目录存在 且 包含至少一个 .md 文件:
           return "from_draft"
       if planning/outline.md 存在:
           return "from_outline"
       if materials/ 目录存在 且 包含文件:
           return "from_materials"
       # 均不存在 → 不应到达此处（Section 0 已处理）
       报错并终止

2. 加载模板（支持继承）
   template_path = "templates/{project_type}/{project_template}.yaml"
   template = Read(template_path)

   # 模板继承：深度合并
   if template.extends:
       parent_path = "templates/{project_type}/{template.extends}.yaml"
       parent_template = Read(parent_path)
       template = deep_merge(parent_template, template)
       # deep_merge 规则：
       #   - 标量字段：子模板覆盖父模板
       #   - 列表字段：子模板替换父模板（不追加）
       #   - 字典字段：递归合并，子模板优先

3. 从模板提取核心结构
   sections          = template.sections            # 章节列表，含 id, name, writer_skill, reviewer_dims
   dependency_graph   = template.dependency_graph    # 章节间依赖关系（DAG）
   review_strategy    = template.review_strategy     # "per_section" | "batch" | "hybrid"

4. 从 config.yaml 提取运行参数
   convergence        = config.convergence           # { max_section_rounds, max_global_rounds, section_score_threshold, global_score_threshold }
   score_weights      = config.score_weights         # 各审阅维度权重，如 { logic: 0.2, detail: 0.15, ... }
   checklist_weight_map = config.checklist_weight_map # checklist 条目到维度的映射权重
   critical_threshold = config.critical_threshold    # 关键缺陷阈值，低于此分数触发 human_needed

5. 合并为运行时上下文
   runtime_ctx = {
       project_type, project_template, input_mode,
       sections, dependency_graph, review_strategy,
       convergence, score_weights, checklist_weight_map, critical_threshold
   }
```

配置校验规则：
- `config.yaml` 不存在 → 报错并终止，提示用户运行 `scholar init`
- `template` 文件不存在 → 报错并终止，列出可用模板
- `sections` 为空 → 报错并终止
- `dependency_graph` 中引用了不存在的 section id → 报错并终止
- `convergence.max_section_rounds` 必须 >= 1 且 <= 10
- `convergence.max_global_rounds` 必须 >= 1 且 <= 5
- `convergence.section_score_threshold` 必须在 0-100 之间
- `convergence.global_score_threshold` 必须在 0-100 之间

### 1.1b Schema 校验（V1 校验点）

Pipeline 启动后，调用 validate.py 校验配置和输入文件：

```
# V1: 校验 config.yaml
result = Bash("python3 scripts/validate.py config config.yaml --format json")
if result.valid == false:
    输出错误信息给用户
    终止 Pipeline

# V1: 根据 input_mode 校验输入完整性
switch(input_mode):
    case "from_materials":
        result = Bash("python3 scripts/validate.py manifest materials/manifest.yaml --format json")
        if result.valid == false: 终止 Pipeline，提示用户修复 manifest.yaml
    case "from_outline":
        result = Bash("python3 scripts/validate.py outline planning/outline.md --format json --project-type {project_type}")
        if result.valid == false: 终止 Pipeline，提示用户修复 outline.md
    case "from_draft":
        验证 sections/ 下至少有一个 .md 文件，否则终止
```

### 1.2 断点恢复

Pipeline 支持从任意中断点恢复执行，通过 `scores.yaml` 记录项目状态。

```
断点恢复流程：

1. 检查 scores.yaml 是否存在
   scores_path = "scores.yaml"
   scores_exists = file_exists(scores_path)

2. 如果不存在 → 新项目初始化
   if not scores_exists:
       scores = {
           phase: "init",
           global_round: 0,
           sections: {}
       }
       for section in runtime_ctx.sections:
           scores.sections[section.id] = {
               status: "pending",       # pending | writing | reviewing | revising | approved | human_needed
               current_round: 0,
               inner_scores: [],        # 每轮内环评分记录
               outer_scores: [],        # 每轮外环评分记录
               reviewer_feedback: null,
               last_updated: now()
           }
       Write(scores_path, scores)
       # V4: 校验 scores.yaml 状态机合法性
       result = Bash("python3 scripts/validate.py scores scores.yaml --format json")
       if result.valid == false:
           尝试自修复（修正非法状态值）
           if 仍失败: 更新 phase → human_needed
       # 后续所有 scores.yaml 写入后均执行 V4 校验

3. 如果存在 → 读取并路由
   else:
       scores = Read(scores_path)
       phase = scores.phase

       switch(phase):

           case "init":
               # 上次在初始化阶段中断，重新开始
               → 继续执行 Section 1.3 入口路由

           case "section_writing":
               # 找到第一个未完成的章节，从 Writer 继续
               target = first(s for s in scores.sections where s.status != "approved")
               if target is null:
                   # 所有章节已完成，推进到外环
                   scores.phase = "global_review"
                   Write(scores_path, scores)
                   → 跳转 Section 4
               else:
                   → 跳转 Section 3，从 target 章节的 Writer 阶段开始

           case "section_review":
               # 找到正在审阅的章节，从 Reviewer 继续
               target = first(s for s in scores.sections where s.status == "reviewing")
               → 跳转 Section 3，从 target 章节的 Reviewer 阶段开始

           case "revision":
               # 找到正在修改的章节，从 Revision Agent 继续
               target = first(s for s in scores.sections where s.status == "revising")
               → 跳转 Section 3，从 target 章节的 Revision 阶段开始

           case "global_review":
               # 进入外环全文验证
               → 跳转 Section 4

           case "human_needed":
               # 输出诊断信息，等待用户介入
               blocked_sections = [s for s in scores.sections where s.status == "human_needed"]
               for s in blocked_sections:
                   输出：
                     - 章节名称: s.id
                     - 当前轮次: s.current_round
                     - 最近评分: s.inner_scores[-1] if exists
                     - 审阅反馈: s.reviewer_feedback
                     - 卡点原因: 评分低于 critical_threshold 或达到 max_section_rounds 仍未收敛
               提示用户：
                 "以上章节需要人工介入。请修改后将 status 改为 'pending' 并重新运行 Pipeline。"

           case "completed":
               提示："项目已完成。是否需要导出最终版本？(导出格式: markdown / latex / docx)"
               等待用户选择 → 调用导出脚本
```

### 1.3 入口路由

根据 `input_mode` 决定 Pipeline 从哪个阶段开始执行。

```
入口路由逻辑：

switch(runtime_ctx.input_mode):

    case "from_materials":
        # 用户提供了原始素材（文献、笔记、数据等），需要从零开始
        # → 执行阶段 1：架构规划
        scores.phase = "init"
        Write(scores_path, scores)
        → 跳转 Section 2（Architect Agent 进行架构规划）

    case "from_outline":
        # 用户已提供 planning/outline.md（大纲）
        # 系统需要补全以下结构化文件：
        validate_file_exists("planning/outline.md")

        # 补全步骤：
        # a) 从 outline.md 解析章节结构，生成 dependency_graph.yaml
        #    - 分析各章节间的引用关系和逻辑依赖
        #    - 构建 DAG 并验证无环
        Agent("architect", task="从 outline.md 生成 dependency_graph.yaml")

        # b) 从 outline.md 提取核心论点，生成 claim_registry.md
        #    - 每个 claim 包含：id, statement, evidence_refs, section_refs
        Agent("architect", task="从 outline.md 提取 claim_registry.md")

        # c) 如果存在 references/ 目录，生成 material_mapping.md
        #    - 将素材映射到各章节
        if dir_exists("references/"):
            Agent("architect", task="生成 material_mapping.md")

        scores.phase = "section_writing"
        Write(scores_path, scores)
        → 跳转 Section 3（开始章节写作-审阅循环）

    case "from_draft":
        # 用户已提供各章节草稿 sections/*.md
        # 系统补全 claim_registry.md，然后进入审阅模式
        validate_dir_exists("sections/")
        draft_files = glob("sections/*.md")
        if len(draft_files) == 0:
            报错："sections/ 目录为空，请提供至少一个章节草稿文件。"

        # 补全 claim_registry.md
        Agent("architect", task="从 sections/*.md 提取 claim_registry.md")

        # 标记所有章节为 writing 完成，直接进入审阅
        for section in runtime_ctx.sections:
            if file_exists(f"sections/{section.id}.md"):
                scores.sections[section.id].status = "reviewing"
                scores.sections[section.id].current_round = 1

        scores.phase = "section_review"
        Write(scores_path, scores)
        → 跳转 Section 3（审阅模式，跳过 Writer 首轮）
```

### 1.4 Dry Run 模式

在正式执行前，可通过 `config.dry_run` 预览完整执行计划。

```
Dry Run 流程：

if config.dry_run == true:

    # 1. 计算章节执行顺序（拓扑排序）
    exec_order = topological_sort(runtime_ctx.dependency_graph)

    # 2. 估算每章节调用次数
    estimated_calls = {}
    for section in exec_order:
        writer_calls = 1                                    # 首轮写作
        reviewer_calls = 1                                  # 首轮审阅
        revision_calls = convergence.max_section_rounds - 1   # 最大修改轮次（最坏情况）
        estimated_calls[section.id] = {
            writer: writer_calls,
            reviewer: reviewer_calls * len(section.reviewer_dims),
            revision: revision_calls
        }

    # 3. 估算外环调用
    outer_calls = convergence.max_global_rounds * len(runtime_ctx.sections)

    # 4. 汇总
    total_agent_calls = sum(
        e.writer + e.reviewer + e.revision
        for e in estimated_calls.values()
    ) + outer_calls

    # 5. 输出执行计划
    输出：
      "=== Dry Run 执行计划 ==="
      "项目类型: {project_type} / {project_template}"
      "输入模式: {input_mode}"
      ""
      "章节执行顺序:"
      for i, section in enumerate(exec_order):
          e = estimated_calls[section.id]
          "  {i+1}. {section.name}"
          "     Writer 调用: {e.writer} 次"
          "     Reviewer 调用: {e.reviewer} 次 ({len(section.reviewer_dims)} 个维度)"
          "     最大修改轮次: {e.revision} 次"
      ""
      "外环全文验证: 最多 {convergence.max_global_rounds} 轮"
      "Agent 调用总估算: {total_agent_calls} 次（最坏情况）"
      ""
      "收敛参数:"
      "  内环最大轮次: {convergence.max_section_rounds}"
      "  外环最大轮次: {convergence.max_global_rounds}"
      "  章节通过分: {convergence.section_score_threshold}, 全文通过分: {convergence.global_score_threshold}"
      "  关键缺陷阈值: {critical_threshold}"

    # 6. 不执行任何 Agent 调用，直接结束
    return
```

---

## 2. 阶段 1：架构规划

本阶段调用 Architect Agent 分析用户材料并构建文档骨架。

### 2.1 调用 Architect Agent

1. 通过 Bash 工具列出 `materials/` 目录下的所有文件
2. 读取每个文件内容（PDF 文件提取文本摘要，Markdown/文本文件直接读取）
3. 读取 `config.yaml` 中的项目类型和模板信息
4. 构造 Architect Agent 的 prompt：

```
你的任务是分析以下研究材料，构建国自然申报书的文档骨架。

## 项目配置
{config.yaml 中的 project 节}

## 材料清单
{materials/ 下每个文件的路径和内容}

## 输出要求
请生成以下 4 个文件：

1. planning/outline.md — 全文大纲
   格式：每个章节包含标题、核心论点（1-2句）、预期篇幅、要点列表

2. planning/dependency_graph.yaml — 章节依赖关系
   格式：与模板中的 dependency_graph 相同的 YAML 结构
   基于模板默认值，根据具体项目微调

3. planning/claim_registry.md — 核心论点注册表
   格式：Markdown 表格
   | 论点ID | 核心论点 | 摘要中表述 | 立项依据中表述 | 研究内容中表述 | 创新点中表述 |

4. planning/material_mapping.md — 材料到章节的映射
   格式：每个章节列出对应的材料文件及其中的关键段落
```

5. 通过 Agent 工具调用 Architect Agent（subagent_type="general-purpose"）

### 2.2 产出物验证

调用后检查：
- planning/outline.md 存在且非空
- planning/dependency_graph.yaml 存在且可被 YAML 解析
- planning/claim_registry.md 存在且非空
- planning/material_mapping.md 存在且非空

任一缺失 → 重试（最多 2 次）→ 仍失败则更新 scores.yaml phase → human_needed

#### V2 Schema 校验

Architect 生成文件后，校验格式正确性：
```
for file_type, path in [("outline", "planning/outline.md"),
                         ("dependency_graph", "planning/dependency_graph.yaml"),
                         ("claim_registry", "planning/claim_registry.md")]:
    result = Bash(f"python3 scripts/validate.py {file_type} {path} --format json --project-type {project_type}")
    if result.valid == false:
        if retry_count < 2: 重新调用 Architect
        else: 更新 scores.yaml phase → human_needed
```

### 2.3 用户确认

输出 outline.md 的内容摘要，请求用户确认或微调：
- 用户确认 → 更新 scores.yaml phase → section_writing，进入阶段 2
- 用户修改 → 等待用户编辑 outline.md 后再次确认

### 2.4 from_outline 模式补全

如果 input_mode == from_outline：
- 跳过 Architect 调用
- 读取用户提供的 planning/outline.md
- 自动生成 dependency_graph.yaml（从模板默认值）
- 自动生成 claim_registry.md（从 outline 中提取核心论点）
- 自动生成 material_mapping.md（如果 materials/ 存在则映射，否则标记为空）

### 2.5 from_draft 模式补全

如果 input_mode == from_draft：
- 跳过 Architect 和 Writer
- 读取 sections/ 下已有章节
- 自动生成 claim_registry.md（从各章节文本中提取核心论点）
- 使用模板默认 dependency_graph

---

## 3. 阶段 2：章节写作-审阅循环（内环）

读取 planning/dependency_graph.yaml，按拓扑排序得到章节执行顺序（priority 值从小到大，同 priority 的章节可并行处理但为简化实现按顺序执行）。

### 3.1 章节迭代主循环

```
FOR 每个章节 section（按拓扑序）:
  IF scores.yaml 中 section.status == "approved": SKIP
  IF scores.yaml 中 section.status == "human_needed": SKIP

  ### 写作阶段
  IF input_mode == "from_draft" AND sections/{section.file} 已存在:
    跳过 Writer，直接进入审阅
  ELSE:
    执行上下文压缩（Section 6.1）：为已完成章节生成摘要
    按 Section 8.1 模板构造 Writer prompt
    通过 Agent 工具调用对应 Writer Agent
    验证 sections/{section.file} 存在且非空
    IF 验证失败 → 重试（最多 2 次）→ 仍失败则标记 human_needed
  更新 scores.yaml: section.status → "reviewing"

  ### 审阅-修改循环
  FOR round = 1 TO convergence.max_section_rounds:
    # 并行调用 3 个章节级 Reviewer
    按 Section 8.2 模板构造 R1、R2、R3 的 prompt
    通过 3 个并行 Agent 调用发出审阅请求
    等待全部返回

    # 保存审阅报告
    将 R1 输出写入 reviews/round_{current_round}/{section编号}_{section名}_R1.md
    将 R2 输出写入 reviews/round_{current_round}/{section编号}_{section名}_R2.md
    将 R3 输出写入 reviews/round_{current_round}/{section编号}_{section名}_R3.md

    # V3: 校验审阅报告格式
    for report_path in [R1_path, R2_path, R3_path]:
        result = Bash(f"python3 scripts/validate.py review_report {report_path} --format json")
        if result.valid == false:
            if retry_count < 2: 重新调用该 Reviewer
            else: 使用 critical_threshold 作为该维度分数，记录到 change_logs/errors.md

    # 解析评分
    从每份审阅报告中提取 Checklist 评分表格
    按 Section 5 的评分聚合逻辑计算章节加权总分

    # 判定
    IF 章节加权总分 ≥ convergence.section_score_threshold:
      更新 scores.yaml: section.status → "approved"
      更新 scores.yaml: section.current_score → 总分
      更新 scores.yaml: section.rounds_used → round
      记录各 reviewer 维度分到 section.last_reviewer_scores
      BREAK

    IF round == convergence.max_section_rounds:
      更新 scores.yaml: section.status → "human_needed"
      记录诊断信息：列出所有未通过的 checklist 项（分数 < 60 的 critical 项 + 分数 < 70 的 high 项）
      BREAK

    # 修改
    更新 scores.yaml: section.status → "revising"
    按 Section 8.3 模板构造 Revision Agent prompt（合并 R1+R2+R3 的修改建议）
    通过 Agent 工具调用 Revision Agent
    验证修改后章节存在且 change_log 已写入
    更新 scores.yaml: section.status → "reviewing", section.rounds_used → round
  END FOR

END FOR
```

### 3.2 内环完成后

所有章节处理完毕后：
- 检查是否有 status == "human_needed" 的章节
  - 有 → 暂停，提示用户哪些章节需要人工介入，等待用户处理后继续
  - 无 → 更新 scores.yaml: phase → "global_review", current_round → 1，进入阶段 3

---

## 4. 阶段 3：全文验证-修改循环（外环）

### 4.1 外环主循环

```
FOR round = 1 TO convergence.max_global_rounds:

  ### 上下文压缩
  执行 Section 6.2 的全文压缩策略：
  为每个章节生成 500 字压缩版

  ### 全文级审阅
  确定本轮需要运行的 Reviewer：
  - 必跑：R4（一致性）、R5（叙事）、R7（格式）
  - 条件触发 R6（可行性）：检查 change_logs/ 中最近一轮是否涉及「研究方案」或「可行性分析」

  定期全文一致性检查：
  IF round % convergence.full_consistency_check_interval == 0:
    R4 使用全文原文而非压缩版（强制全面检查）

  并行调用需要运行的 Reviewer（按 Section 8.2 的全文级模板）
  保存审阅报告到 reviews/round_{current_round}/global_R{N}.md

  ### 评分聚合
  按 Section 5 的全文级评分逻辑计算加权总分
  更新 scores.yaml: global.round_{round} 记录各维度分数和总分
  更新 change_history: 统计本轮 critical/major/minor 数量

  ### 收敛判定
  条件 A: 加权总分 ≥ convergence.global_score_threshold
  条件 B: 本轮审阅意见中 critical == 0 AND major ≤ convergence.max_major_issues

  IF A AND B:
    更新 scores.yaml: phase → "completed"
    运行 scripts/export_docx.py 导出最终版本
    输出完成摘要：最终分数、总轮次、各维度分数趋势、token 消耗
    STOP

  IF round == convergence.max_global_rounds AND NOT (A AND B):
    更新 scores.yaml: phase → "human_needed"
    输出诊断报告：
      - 各维度分数趋势（每轮的分数变化）
      - 反复不过的 checklist 项列表
      - 卡住的原因分析
    STOP

  ### 分数回退检测
  IF round > 1:
    IF 本轮 weighted_total < 上一轮 weighted_total:
      下一轮强制全文重审：所有章节重新进入内环，不使用影响分析
      在 scores.yaml 中标注 force_full_recheck: true
      CONTINUE（跳过下面的增量重审，直接进入下一轮）

  ### 修改与影响分析
  合并 R4-R7 的审阅意见
  按 Section 8.3 模板调用 Revision Agent

  # 脚本辅助交叉引用检测
  运行 scripts/check_cross_refs.py sections/ → 获取章节间引用关系图
  读取 Revision Agent 输出的 change_log

  确定受影响章节：
  1. change_log 中 Revision Agent 标注的受影响章节
  2. check_cross_refs 检测到的：如果被修改章节被其他章节引用，引用方自动标记为受影响
  3. 取两者的并集

  ### 增量重审
  只对受影响章节重新触发阶段 2 内环（Section 3）
  这些章节的 scores.yaml status 重置为 "reviewing"
  更新 scores.yaml: current_round → round + 1

END FOR
```

### 4.2 外环完成后的输出

#### V5 最终完整性校验

```
results = Bash("python3 scripts/validate.py all . --format json")
输出完整性报告（仅作参考，不阻塞已完成的项目）
```

无论以何种方式结束（completed / human_needed），都输出以下信息：
- 总运行轮次（内环总轮次 + 外环轮次）
- 各章节最终分数
- 全文各维度分数
- 累计 token 消耗（从 scores.yaml 的 token_usage 读取）
- 如果是 completed：导出的 .docx 文件路径
- 如果是 human_needed：需要人工关注的具体问题列表

---

## 5. 评分聚合逻辑

### 5.1 Checklist 条目 → Reviewer 维度分

每个 Reviewer 对其 checklist 中的每条 criterion 打分（0-100）。按 weight 加权聚合为该 Reviewer 的维度分：

- critical 权重 = 3
- high 权重 = 2
- medium 权重 = 1
- 维度分 = Σ(条目分 × 条目权重) / Σ(条目权重)

**Critical 短路规则**：任一 critical 条目分数 < critical_threshold（默认 60）时，该维度直接标红（flagged）。标红维度的处理：
1. 在审阅报告中显著标注
2. 章节/全文总分在加权聚合后额外扣减 10 分
3. 修改建议中该 critical 条目标为最高优先级

### 5.2 章节级评分（内环，R1-R3）

```
section_score = logic_score × 0.40 + de_ai_score × 0.25 + completeness_score × 0.35

IF 任一维度被标红:
  section_score = max(section_score - 10, 0)

判定: section_score ≥ section_score_threshold → 通过
```

**计算示例**：
```
章节"立项依据"第 1 轮审阅：
  R1(Logic):       L1=85(high/2), L2=70(critical/3), L3=80(high/2)
                   → (85×2 + 70×3 + 80×2) / (2+3+2) = 76.4
                   → L2=70 ≥ 60 → 不触发短路
  R2(De-AI):       D1=90(medium/1), D2=75(high/2), D3=85(medium/1)
                   → (90×1 + 75×2 + 85×1) / (1+2+1) = 81.3
  R3(Completeness): C1=80(high/2), C2=65(critical/3), C3=90(medium/1), C4=70(critical/3)
                   → (80×2 + 65×3 + 90×1 + 70×3) / (2+3+1+3) = 73.9
                   → C2=65 ≥ 60, C4=70 ≥ 60 → 不触发短路

  章节加权总分 = 76.4×0.40 + 81.3×0.25 + 73.9×0.35 = 77.0
  → 77.0 < section_score_threshold(80) → 进入修改
```

### 5.3 全文级评分（外环，R4-R7）

**R6 运行时（正常情况）**：
```
global_score = consistency × 0.30 + narrative × 0.35 + feasibility × 0.20 + format × 0.15
```

**R6 未运行但有历史分数时**：
```
feasibility_score = 上一轮的 feasibility 分数
global_score = consistency × 0.30 + narrative × 0.35 + feasibility_score × 0.20 + format × 0.15
```

**R6 从未运行过（首轮即未触发）**：
```
重新归一化权重（排除 feasibility 的 0.20）：
  consistency: 0.30 / 0.80 = 0.375
  narrative:   0.35 / 0.80 = 0.4375
  format:      0.15 / 0.80 = 0.1875
global_score = consistency × 0.375 + narrative × 0.4375 + format × 0.1875
```

如果任一维度被标红：global_score = max(global_score - 10, 0)

### 5.4 评分解析

从 Reviewer 的审阅报告中提取评分表格。预期格式：
```
| ID | Criterion | Score | Justification |
```

解析每行的 ID 和 Score 字段。如果解析失败 → 触发 Section 7 的错误处理流程。

---

## 6. 上下文预算管理

为防止后期 agent 上下文溢出，对每类 agent 的输入实施压缩策略。

### 6.1 Section Writer 的输入压缩

为每个已完成章节生成 200-300 字摘要，作为后续 Writer 的参考上下文：
- 在主会话中直接执行摘要生成（不需要独立 agent）
- 读取 sections/章节名.md → 提取核心论点和关键数据 → 生成摘要
- 存入 sections/summaries/章节名_summary.md
- Writer Agent 接收的前序章节上下文只包含这些摘要，不包含全文

**预算估算**：
- 章节大纲 ≈ 1K token
- Checklist ≈ 2K token
- 前序章节摘要（最多 6 章 × 300字）≈ 3K token
- 素材片段 ≈ 3-5K token
- claim_registry ≈ 2K token
- **总计 ≈ 11-13K token**，在 sub-agent 上下文窗口内可控

### 6.2 Global Reviewer 的输入压缩

在调用全文级 Reviewer（R4-R7）之前，主会话执行以下压缩步骤：
- 对每个章节生成 500 字压缩版，存入 sections/summaries/章节名_compressed.md
- 被影响分析标记为"重点关注"的章节传递原文，其余传递压缩版
- R4（一致性）额外接收完整的 claim_registry.md
- R7（格式）主要依赖脚本输出，LLM 只处理脚本无法覆盖的部分

**预算估算**：
- 全文压缩版（7 章 × 500字）≈ 6K token
- 重点章节原文（1-2 章）≈ 5K token
- Checklist ≈ 2K token
- claim_registry ≈ 2K token
- **总计 ≈ 15-17K token**，在 sub-agent 上下文窗口内可控

### 6.3 溢出降级策略

如果实际输入超出预算（Agent 调用返回截断或异常）：
1. 前序章节摘要缩减到 100 字/章
2. 全文压缩版缩减到 300 字/章
3. 素材片段只保留 material_mapping 中标注为"关键"的部分

---

## 7. 错误处理

### 7.1 Writer 产出异常

**检测**：调用 Writer Agent 后，检查 sections/{章节}.md 是否存在且非空
**恢复**：
1. 重新调用 Writer Agent（最多重试 2 次）
2. 仍失败 → 更新 scores.yaml 该章节 status → "human_needed"
3. 记录错误到 change_logs/errors.md：时间、章节名、错误描述

### 7.2 Reviewer 评分解析失败

**检测**：审阅报告中未找到预期的评分表格格式（| ID | Criterion | Score | Justification |）
**恢复**：
1. 重新调用 Reviewer（新鲜上下文，最多重试 2 次）
2. 仍失败 → 该维度使用上一轮分数
3. 首轮即解析失败 → 该维度使用 critical_threshold（默认 60）作为默认分
4. 记录到 change_logs/errors.md

### 7.3 脚本执行失败

**检测**：Python 脚本（count_words.py、check_format.py 等）退出码 ≠ 0
**恢复**：
1. 记录错误到 change_logs/errors.md
2. 跳过该检查项，在 scores.yaml 中标注 script_error: true
3. 不阻塞整体流程

### 7.4 外环分数震荡

**检测**：连续 2 轮全文总分变化 < 2 分且未达 global_score_threshold
**恢复**：
1. 更新 scores.yaml: phase → "human_needed"
2. 输出诊断报告：
   - 每个维度的分数趋势（过去各轮的分数列表）
   - 反复不过的 checklist 项（连续 2 轮分数 < 60 的条目）
   - 可能的卡点原因分析

### 7.5 上下文窗口溢出

**检测**：Agent 调用返回截断信号或异常错误
**恢复**：
1. 启用更激进的摘要策略：
   - 前序章节摘要缩减到 100 字/章
   - 全文压缩版缩减到 300 字/章
   - 素材片段只保留 material_mapping 中标注为"关键"的部分
2. 以降级模式重试 Agent 调用
3. 仍失败 → 标记 human_needed

### 7.6 Token 使用追踪

每次 Agent 调用后，更新 scores.yaml 中的 token_usage 字段：

```yaml
token_usage:
  total_input: 0
  total_output: 0
  by_agent:
    architect: { input: 0, output: 0, calls: 0 }
    writer: { input: 0, output: 0, calls: 0 }
    reviewer: { input: 0, output: 0, calls: 0 }
    revision: { input: 0, output: 0, calls: 0 }
```

注意：实际 token 数可能无法精确获取（取决于 Claude Code API 的返回信息）。如果无法获取，记录调用次数作为替代指标。

### 7.7 所有错误的统一日志

所有错误和异常记录到 change_logs/errors.md，格式：
```
## [时间戳] [错误类型]
- 章节/阶段：{位置}
- 错误描述：{描述}
- 恢复策略：{采取的措施}
- 结果：{成功/仍失败}
```

---

## 8. Agent 调用模板

以下是编排器调用各类 agent 时的 prompt 构造模板。

### 8.1 调用 Writer Agent

对于每个章节，按以下模板构造 Writer 的 prompt：

```
你的任务是撰写国自然申报书的「{章节名}」部分。

## 章节大纲
{从 planning/outline.md 中提取该章节的大纲部分}

## 评审标准（写作时请对照，你将被这些标准审阅）
{从 templates/nsfc/checklists/{章节}.yaml 中提取完整 checklist}

## 前序章节摘要（保持上下文连贯）
{从 sections/summaries/ 读取已完成章节的摘要，按依赖顺序排列}

## 相关素材
{从 planning/material_mapping.md 中提取该章节对应的素材内容}

## 论点注册表（保持核心论点表述一致）
{planning/claim_registry.md 全文}

请将完成的章节写入 sections/{编号}_{章节名}.md
```

通过 Agent 工具调用：
- subagent_type: "general-purpose"
- 读取对应 Writer SKILL.md 的内容，与上述 prompt 合并为完整指令

### 8.2 调用 Reviewer Agent（两步法）

章节级审阅时，并行调用 R1 + R2 + R3。每个 Reviewer 的 prompt 模板：

```
请对以下章节进行{审阅维度}审阅。

## 待审阅章节
{sections/章节名.md 的完整文本}

## 评审标准
{从 checklist 中提取该 Reviewer 对应维度的条目}

## 审阅流程（严格遵循两步法）

### 第一步：自由分析
通读全文，从{维度}角度自由分析。不看 checklist，不限格式，充分推理。

### 第二步：对照 Checklist 评分
对照上述评审标准，逐条打分（0-100）。输出格式：

| ID | Criterion | Score | Justification |
|----|-----------|-------|---------------|

### 第三步：修改建议
按严重级别排序输出：
- [Critical] ...
- [Major] ...
- [Minor] ...
```

全文级审阅（R4-R7）的 prompt 类似，但输入替换为全文压缩版 + 重点章节原文。

调用方式：3 个章节级 Reviewer 通过 3 个并行 Agent 调用。

### 8.3 调用 Revision Agent

```
请修改「{章节名}」章节。

## 原文
{sections/章节名.md 的完整文本}

## 审阅意见（按严重级别排序：critical → major → minor）
{合并该章节所有 Reviewer 的审阅报告}

## 论点注册表
{planning/claim_registry.md}

请完成以下任务：
1. 按审阅意见逐条修改章节，将修改后内容写入 sections/{章节名}.md
2. 将修改记录写入 change_logs/round_{N}_changes.md，每条包含：
   - 修改位置（章节名 + 段落位置）
   - 修改内容摘要
   - 对应的审阅意见 ID
   - 受影响的其他章节列表及原因
3. 如果修改涉及 claim_registry 中的核心论点，同时更新 planning/claim_registry.md
```

### 8.4 审阅报告存储

每轮审阅的报告存储路径：
- 章节级：reviews/round_{N}/{章节编号}_{章节名}_R{1,2,3}.md
- 全文级：reviews/round_{N}/global_R{4,5,6,7}.md
