# References 接入改造方案

## 实施状态

已落地到当前写作 workflow：

- 已新增 reference registry 和 schema。
- `taskpack` 已输出 `reference_inputs`。
- repo-local skill、Codex custom agents 和平台无关 prompts 已要求读取 `reference_inputs`。
- `review_result` 与 `revision_log` 已支持 `reference_basis`。
- README、Codex 使用文档、Codex 架构文档和 schemas 文档已同步。

## 目标

把 `scholar-writing/references/` 从“旧 skill 中零散引用的资料目录”升级为 Codex 与 Claude Code 都能使用的正式质量规则层。

改造完成后，用户仍然只需要在 Codex 或 Claude Code 中用自然语言触发 `scholar-writing`。agent 在后台自动选择和加载必要 references，用这些资料约束规划、写作、审阅和修订。

## 当前问题

`references/` 包含本项目学术写作质量的关键知识：

| 文件 | 价值 |
| --- | --- |
| `STYLE_GUIDE_ZH.md` | 中文学术写作风格、句式、段落、标点、衔接规则 |
| `DEAI_PATTERNS_ZH.md` | 中文 AI 写作痕迹检测与改写规则 |
| `NSFC_GUIDE.md` | 国自然申报书写作要求、评审侧重点、常见扣分项 |
| `NSFC_STRUCTURE_ZH.md` | 国自然各章节结构蓝图 |
| `SENTENCE_PATTERNS_ZH.md` | 通用学术句式库 |
| `patterns/00_通用.md` | 通用过渡、递进、论证和衔接句式 |
| `patterns/01_摘要.md` 至 `patterns/07_研究基础.md` | 分章节写作句式模板 |

旧 Claude Code 角色资产已经大量引用这些资料。当前 Codex 新流程的入口、agent 配置、通用 prompt 和 taskpack 尚未正式接入它们。

直接后果：

- Codex writer 缺少 NSFC 章节结构约束。
- Codex reviewer 缺少 de-AI、格式、叙事、可行性等专项规则来源。
- Codex revision 无法把审阅意见映射回具体写作规范。
- `references/` 的知识无法被 schema、测试和 taskpack 验证。
- Claude Code 与 Codex 的质量基线可能逐步分叉。

## 设计原则

1. **references 是规则输入。** 用户素材放在项目目录的 `materials/`；框架规则放在仓库的 `scholar-writing/references/`。
2. **按任务选择资料。** 不把整个 `references/` 一次塞给 agent，避免上下文浪费和规则互相干扰。
3. **taskpack 明确声明引用。** agent 读取哪些 references 必须可见、可测试、可复现。
4. **Python controller 做选择，agent 做执行。** 资料选择逻辑进入确定性代码，避免每次由 LLM 临场判断。
5. **Codex 和 Claude Code 共享同一套 reference registry。** 平台 adapter 只负责加载方式，规则映射不重复维护。
6. **引用路径使用相对路径。** 文档、taskpack、测试 fixture 中不写入本机绝对路径。

## 目标用户体验

用户在 Codex 中输入：

```text
使用 scholar-writing 审阅优化 ./my-proposal 的国自然初稿。
```

Codex 后台应执行：

1. controller 判断当前项目从 `sections/*.md` 进入审阅。
2. controller 生成 taskpack。
3. taskpack 包含 `reference_inputs`，例如：

```yaml
reference_inputs:
  style:
    - scholar-writing/references/STYLE_GUIDE_ZH.md
  de_ai:
    - scholar-writing/references/DEAI_PATTERNS_ZH.md
  nsfc:
    - scholar-writing/references/NSFC_GUIDE.md
    - scholar-writing/references/NSFC_STRUCTURE_ZH.md
  section_patterns:
    - scholar-writing/references/patterns/00_通用.md
    - scholar-writing/references/patterns/02_立项依据.md
```

4. reviewer 根据这些 references 输出结构化审阅结果。
5. revision 根据审阅结果和同一组 references 做定向修改。
6. controller 用 `scores.yaml` 记录状态并决定是否进入下一轮。

用户不需要手动打开 references，也不需要手动运行 CLI。

## 架构改造

### 1. Reference Registry

新增一个确定性的 registry，集中描述每个 reference 的用途、适用阶段、适用角色和适用章节。

建议新增：

```text
scholar_writing/core/references.py
scholar-writing/schemas/reference_registry.schema.yaml
scholar-writing/config/reference_registry.yaml
```

`reference_registry.yaml` 负责声明规则资产：

```yaml
version: 1
references:
  style_zh:
    path: scholar-writing/references/STYLE_GUIDE_ZH.md
    applies_to:
      project_types: [nsfc, paper]
      agent_roles: [writer, reviewer, revision]
      actions: [run_writer, run_reviewers, run_revision]
    purpose: 中文学术写作风格规则

  deai_zh:
    path: scholar-writing/references/DEAI_PATTERNS_ZH.md
    applies_to:
      project_types: [nsfc, paper]
      agent_roles: [reviewer, revision]
      actions: [run_reviewers, run_revision]
      review_dimensions: [de_ai]
    purpose: AI 写作痕迹检测与改写规则

  nsfc_structure:
    path: scholar-writing/references/NSFC_STRUCTURE_ZH.md
    applies_to:
      project_types: [nsfc]
      agent_roles: [architect, writer, reviewer, revision]
      actions: [run_architect, run_writer, run_reviewers, run_revision]
    purpose: 国自然章节结构规则

  nsfc_guide:
    path: scholar-writing/references/NSFC_GUIDE.md
    applies_to:
      project_types: [nsfc]
      agent_roles: [architect, reviewer]
      actions: [run_architect, run_reviewers]
    purpose: 国自然评审要求和扣分项

  sentence_patterns_zh:
    path: scholar-writing/references/SENTENCE_PATTERNS_ZH.md
    applies_to:
      project_types: [nsfc, paper]
      agent_roles: [writer, revision]
      actions: [run_writer, run_revision]
    purpose: 通用句式库
```

分章节 patterns 用单独映射维护：

```yaml
section_patterns:
  nsfc:
    "01_摘要": scholar-writing/references/patterns/01_摘要.md
    "02_立项依据": scholar-writing/references/patterns/02_立项依据.md
    "03_研究内容": scholar-writing/references/patterns/03_研究内容.md
    "04_研究方案": scholar-writing/references/patterns/04_研究方案.md
    "05_可行性分析": scholar-writing/references/patterns/05_可行性分析.md
    "06_创新点": scholar-writing/references/patterns/06_创新点.md
    "07_研究基础": scholar-writing/references/patterns/07_研究基础.md
```

### 2. Reference Selector

新增 `select_references()`，由 controller 根据 taskpack 上下文选择资料。

建议接口：

```python
def select_references(
    *,
    project_type: str,
    action: str,
    agent_role: str,
    target_section: str | None = None,
    review_dimensions: list[str] | None = None,
    language: str = "zh",
) -> dict:
    ...
```

选择规则：

| 场景 | 必选 references |
| --- | --- |
| `run_architect` + `nsfc` | `NSFC_GUIDE.md`、`NSFC_STRUCTURE_ZH.md` |
| `run_writer` + 任意中文项目 | `STYLE_GUIDE_ZH.md`、`SENTENCE_PATTERNS_ZH.md`、`patterns/00_通用.md` |
| `run_writer` + NSFC 指定章节 | 对应 `patterns/XX_章节.md`、`NSFC_STRUCTURE_ZH.md` |
| `run_reviewers` + `logic` | `NSFC_STRUCTURE_ZH.md`、对应章节 pattern |
| `run_reviewers` + `de_ai` | `DEAI_PATTERNS_ZH.md`、`STYLE_GUIDE_ZH.md` |
| `run_reviewers` + `completeness` | `NSFC_GUIDE.md`、`NSFC_STRUCTURE_ZH.md` |
| `run_reviewers` + `format` | `STYLE_GUIDE_ZH.md`、`NSFC_GUIDE.md` |
| `run_revision` | 最近审阅维度对应 references + writer references |

### 3. Taskpack 扩展

`taskpack` 必须增加 `reference_inputs` 字段。

建议结构：

```yaml
reference_inputs:
  required:
    - id: style_zh
      path: scholar-writing/references/STYLE_GUIDE_ZH.md
      reason: 写作风格与标点规则
    - id: nsfc_structure
      path: scholar-writing/references/NSFC_STRUCTURE_ZH.md
      reason: 国自然章节结构约束
  section_specific:
    - id: pattern_02_lixiangyiju
      path: scholar-writing/references/patterns/02_立项依据.md
      reason: 立项依据句式模板
  optional:
    - id: sentence_patterns_zh
      path: scholar-writing/references/SENTENCE_PATTERNS_ZH.md
      reason: 句式替换和修订参考
```

同时扩展 schema：

```yaml
reference_inputs:
  type: object
  properties:
    required:
      type: array
      items:
        $ref: "#/$defs/reference_input"
    section_specific:
      type: array
      items:
        $ref: "#/$defs/reference_input"
    optional:
      type: array
      items:
        $ref: "#/$defs/reference_input"
```

每个 reference input：

```yaml
reference_input:
  type: object
  required: [id, path, reason]
  properties:
    id:
      type: string
    path:
      type: string
    reason:
      type: string
    max_extract:
      type: [integer, "null"]
    sections:
      type: array
      items:
        type: string
```

### 4. Prompt 更新

通用 prompt 需要声明 references 的优先级。

`scholar_writing/prompts/writer.md` 应加入：

```markdown
你必须读取 task pack 中的 `reference_inputs`。
写作时按以下优先级使用规则：
1. 用户明确要求
2. task pack 的写作目标和写入边界
3. `reference_inputs.required`
4. `reference_inputs.section_specific`
5. `reference_inputs.optional`

如果 references 与用户材料冲突，保留用户材料事实，并在交付中说明冲突。
不得用 references 虚构项目事实。
```

`scholar_writing/prompts/reviewer.md` 应加入：

```markdown
审阅必须引用 task pack 中相关 references 的规则来源。
每条 major 或 critical 问题都应说明违反了哪类规则：
- 结构规则
- 风格规则
- de-AI 规则
- 完备性规则
- 格式规则
```

`scholar_writing/prompts/revision.md` 应加入：

```markdown
修订时必须同时参考 review_result 和 `reference_inputs`。
修订日志中记录每类修改对应的规则来源。
如果某项修改需要改变核心论点或新增事实，先请求用户确认。
```

`scholar_writing/prompts/architect.md` 应加入：

```markdown
规划国自然项目时必须参考 NSFC structure 和 guide references。
规划产物应体现章节使命、核心论点、科学问题、研究内容和评审关注点之间的对应关系。
```

### 5. Repo-local Skill 更新

`.agents/skills/scholar-writing/SKILL.md` 需要明确：

- `taskpack` 是 agent handoff 的事实源。
- `reference_inputs` 是质量规则输入。
- agent 调用前必须读取 taskpack 中列出的 references。
- agent 不应自行遍历整个 `references/`。
- 遇到上下文过大时，优先读取 `required`，再读 `section_specific`，最后读 `optional`。

建议加入操作规则：

```markdown
调用 agent 前，先检查 taskpack 中的 `reference_inputs`。
把这些引用文件作为质量规则传递，不要当作用户提供的事实证据。
除非用户明确要求完整规则审计，不要遍历读取 `scholar-writing/references/` 下的全部文件。
```

### 6. Codex Agent 配置更新

`.codex/agents/scholar-writer.toml` 增加：

```toml
- Read taskpack.reference_inputs before writing.
- Treat references as style, structure, and review-rule constraints.
- Use section-specific pattern files when target_section is present.
```

`.codex/agents/scholar-reviewer.toml` 增加：

```toml
- Review against taskpack.reference_inputs.
- Cite the rule category for each major or critical issue.
- Use DEAI_PATTERNS_ZH.md for de-AI review dimensions when provided.
```

`.codex/agents/scholar-revision.toml` 增加：

```toml
- Apply review_result together with taskpack.reference_inputs.
- Record reference-backed changes in revision_log.
```

`.codex/agents/scholar-architect.toml` 增加：

```toml
- Use NSFC guide and structure references when planning NSFC proposals.
- Keep claim registry aligned with section missions from references.
```

### 7. Review Result 与 Revision Log 扩展

审阅结果应记录问题对应的规则来源，便于修订 agent 精准处理。

建议扩展 `review_result`：

```yaml
issues:
  - severity: major
    dimension: de_ai
    location: sections/02_立项依据.md
    finding: 开头使用公式化背景句，信息密度低。
    reference_basis:
      - id: deai_zh
        rule: 公式化开头模式
```

修订日志应记录修改依据：

```yaml
changes:
  - file: sections/02_立项依据.md
    summary: 重写开篇段落，直接切入具体问题。
    reference_basis:
      - id: deai_zh
      - id: style_zh
```

对应 schema 需要补充 `reference_basis`。

### 8. 测试策略

新增测试应覆盖 selector、taskpack、schema、prompt contract 和 CLI 输出。

建议测试文件：

```text
tests/test_references.py
tests/test_taskpack_references.py
tests/test_review_result_references.py
```

核心用例：

1. `run_architect` + `nsfc` 返回 `NSFC_GUIDE.md` 和 `NSFC_STRUCTURE_ZH.md`。
2. `run_writer` + `02_立项依据` 返回 `STYLE_GUIDE_ZH.md`、`SENTENCE_PATTERNS_ZH.md`、`patterns/00_通用.md`、`patterns/02_立项依据.md`。
3. `run_reviewers` + `de_ai` 返回 `DEAI_PATTERNS_ZH.md` 和 `STYLE_GUIDE_ZH.md`。
4. `run_revision` 继承最近 review_result 的维度 references。
5. 所有 `reference_inputs.path` 都是相对路径。
6. taskpack schema 接受 `reference_inputs`。
7. 缺失 reference 文件时报明确错误。
8. `uv run scholar-writing taskpack examples/from-outline --format json` 输出包含 `reference_inputs`。

## 分阶段执行计划

### Phase 1：建立 registry 和 selector

**目标：** controller 能确定性选择 references。

**修改文件：**

- 新增 `scholar-writing/config/reference_registry.yaml`
- 新增 `scholar-writing/schemas/reference_registry.schema.yaml`
- 新增 `scholar_writing/core/references.py`
- 新增 `tests/test_references.py`

**验收条件：**

- registry schema 校验通过。
- selector 能按项目类型、action、agent_role、章节和审阅维度返回稳定结果。
- 所有返回路径均为相对路径。

### Phase 2：把 references 写入 taskpack

**目标：** agent handoff 中显式包含质量规则输入。

**修改文件：**

- 修改 `scholar_writing/core/taskpack.py`
- 修改 `scholar-writing/schemas/taskpack.schema.yaml`
- 修改 `tests/test_core.py`
- 新增或修改 `tests/test_taskpack_references.py`

**验收条件：**

- `taskpack` 输出包含 `reference_inputs`。
- `examples/from-materials` 的 taskpack 包含 NSFC guide 和 structure。
- `examples/from-outline` 的 taskpack 包含 writer 所需 style、sentence patterns 和 NSFC structure。
- `examples/from-draft` 的 taskpack 包含 reviewer 所需 style、de-AI 或结构规则。

### Phase 3：让 prompts、repo-local skill 和 Codex adapter 消费 references

**目标：** agent 明确把 references 当作质量规则。

**修改文件：**

- 修改 `.agents/skills/scholar-writing/SKILL.md`
- 修改 `.codex/agents/scholar-architect.toml`
- 修改 `.codex/agents/scholar-writer.toml`
- 修改 `.codex/agents/scholar-reviewer.toml`
- 修改 `.codex/agents/scholar-revision.toml`
- 修改 `scholar_writing/prompts/architect.md`
- 修改 `scholar_writing/prompts/writer.md`
- 修改 `scholar_writing/prompts/reviewer.md`
- 修改 `scholar_writing/prompts/revision.md`
- 修改 `tests/test_codex_adapter.py`

**验收条件：**

- repo-local skill 明确要求读取 taskpack 的 `reference_inputs`。
- writer/reviewer/revision/architect prompt 都说明 references 的使用方式。
- 测试能检查 repo-local skill 和 Codex adapter 文案中存在 `reference_inputs` 契约。

### Phase 4：扩展审阅与修订事件 schema

**目标：** 审阅问题和修订记录能追踪规则来源。

**修改文件：**

- 修改 `scholar-writing/schemas/review_result.schema.yaml`
- 修改 `scholar-writing/schemas/revision_log.schema.yaml`
- 修改 `scholar_writing/core/workflow.py`
- 修改 `tests/test_core.py`
- 新增 `tests/test_review_result_references.py`

**验收条件：**

- review_result 支持 `reference_basis`。
- revision_log 支持 `reference_basis`。
- `advance` 能保留或消费这些字段。
- critical 和 major 问题能携带规则来源。

### Phase 5：文档同步

**目标：** 用户知道 references 会自动生效，开发者知道如何维护 registry。

**修改文件：**

- 修改 `README.md`
- 修改 `docs/codex-getting-started.md`
- 修改 `docs/codex-architecture.md`
- 修改 `scholar-writing/schemas/README.md`

**验收条件：**

- 用户文档说明 references 会由 agent 自动加载。
- 开发者文档说明新增 reference 的步骤。
- 文档中不写入本机绝对路径。

## 建议实现顺序

1. 先做 Phase 1 和 Phase 2，让 taskpack 真实携带 `reference_inputs`。
2. 再做 Phase 3，让 repo-local skill 和 agents 按 taskpack 使用 references。
3. 然后做 Phase 4，把审阅与修订的规则来源记录进事件。
4. 最后做 Phase 5，同步 README 和架构文档。

这个顺序能先保证数据链路成立，再优化 agent 行为和文档表达。

## 风险与处理

| 风险 | 处理 |
| --- | --- |
| references 过多导致上下文膨胀 | selector 分 `required`、`section_specific`、`optional`，agent 先读必要资料 |
| references 与用户材料冲突 | 用户材料作为事实来源，references 作为表达与结构规则；冲突写入交付说明 |
| Codex agent 忘记读取 references | skill、agent toml、prompt、adapter tests 同时约束 |
| Claude Code 与 Codex 规则分叉 | registry 成为共享规则源，旧 skill 后续逐步改为引用 registry |
| 新增 reference 后无人维护映射 | registry schema 和测试要求所有 path 存在 |

## 完成标准

改造完成应满足：

- `taskpack` 对每个 action 都能输出合理的 `reference_inputs`。
- Codex writer/reviewer/revision 能按 taskpack 引用 references。
- review_result 和 revision_log 能记录规则来源。
- 测试覆盖 selector、schema、taskpack 和 adapter contract。
- README 中的用户流程仍保持自然语言入口，不要求用户手动读取 references。
- 所有示例和文档使用相对路径。
