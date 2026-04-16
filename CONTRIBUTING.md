# 贡献指南

感谢你对 ScholarWriting 的关注! 本文档说明如何参与项目贡献。

## 如何贡献

### 报告问题

通过 GitHub Issues 提交问题报告，请包含：
- 问题的详细描述
- 复现步骤
- 期望行为与实际行为
- 运行环境信息（Claude Code 版本、Python 版本、操作系统）

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更：`git commit -m "feat: 描述你的变更"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: 新功能
fix: 修复问题
docs: 文档变更
refactor: 代码重构（不影响功能）
test: 添加或修改测试
chore: 构建流程或辅助工具变更
```

## 开发指南

### 添加新的项目模板

1. 在 `scholar-writing/templates/` 下创建新目录
2. 创建 `base.yaml`，定义章节结构和依赖图
3. 创建 `checklists/` 下的评审检查清单
4. 可通过 `extends` 字段继承已有模板

模板 YAML 结构示例：

```yaml
type: your_type
extends: nsfc/base          # 可选，继承基础模板

sections:
  - name: 章节名
    file: 01_章节名.md
    checklist: checklists/01_章节名.yaml
    writer: writer/your_type/章节名

dependency_graph:
  章节A:
    depends_on: []
    priority: 1
  章节B:
    depends_on: [章节A]
    priority: 2
```

### 添加新的 Writer Agent

1. 在 `scholar-writing/skills/writer/` 下创建目录
2. 编写 `SKILL.md`，包含 YAML frontmatter 和写作指令
3. 创建 `config.yaml` 配置文件

SKILL.md frontmatter 格式：

```yaml
---
name: writer-section-name
description: 该章节的写作策略简述
allowed-tools: [Read, Write, Edit, Bash]
---
```

### 添加新的 Reviewer Agent

1. 在 `scholar-writing/skills/reviewer/` 下创建目录（如 `R9_your_dimension/`）
2. 编写 `SKILL.md`，定义审阅维度和评分标准
3. 在对应模板的 `review_strategy` 中注册新 Reviewer
4. 更新 `config/default_config.yaml` 中的评分权重

### Checklist 编写规范

- 使用正面指令表述（"应当包含 X" 而非 "不要遗漏 X"）
- 每条标准指定权重级别：`critical` / `high` / `medium`
- 复杂标准可附带 `few_shot` 示例
- 为每条标准分配唯一 ID（如 `L1`、`D2`、`C3`）

### 运行测试

```bash
cd tests
python -m pytest test_validate.py -v
python -m pytest test_scripts.py -v
```

### Schema 校验

修改数据结构后，确保通过 Schema 校验：

```bash
python scholar-writing/scripts/validate.py all <project_dir>
```

## 代码风格

- Python 代码遵循 PEP 8
- YAML 文件使用 2 空格缩进
- SKILL.md 使用标准 Markdown 格式
- 中文文档使用全角标点
- 函数级注释包含：功能描述、输入参数、返回值

## 许可证

提交贡献即表示你同意将代码以 Apache License 2.0 授权。
