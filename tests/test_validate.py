#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py 的测试套件。
通过 subprocess 调用 validate.py，验证各数据类型的校验逻辑。

测试覆盖：
  - config: 合法/缺字段/非法枚举/权重语义
  - scores: 合法/非法状态
  - dependency_graph: 合法/引用缺失/有环
  - manifest: 合法/缺字段/非法类型
  - review_report: 合法/无frontmatter/缺表格/错误dimension
  - outline: 合法(nsfc)
  - claim_registry: 合法
"""

import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

# 项目根目录和脚本路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = PROJECT_ROOT / 'scholar_writing' / 'resources' / 'scripts' / 'validate.py'


def run_validate(data_type, file_path, extra_args=None):
    """
    调用 validate.py 并返回解析后的 JSON 结果和退出码。

    输入参数：
      data_type: str - 数据类型
      file_path: str - 文件路径
      extra_args: list|None - 额外命令行参数

    输出返回值：
      tuple(dict, int) - (JSON 结果字典, 退出码)
    """
    cmd = [sys.executable, str(VALIDATE_SCRIPT), data_type, file_path, '--format', 'json']
    if extra_args:
        cmd.extend(extra_args)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result = {'valid': False, 'errors': [{'message': f'JSON 解析失败: {proc.stdout} {proc.stderr}'}], 'warnings': []}
    return result, proc.returncode


def write_yaml(content):
    """
    将 YAML 内容写入临时文件。

    输入参数：
      content: str - YAML 内容

    输出返回值：
      str - 临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix='.yaml', prefix='test_validate_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def write_md(content):
    """
    将 Markdown 内容写入临时文件。

    输入参数：
      content: str - Markdown 内容

    输出返回值：
      str - 临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix='.md', prefix='test_validate_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


# ======================== Config 测试 ========================

def test_config_valid():
    """测试合法的 config 文件"""
    path = write_yaml("""
project:
  type: nsfc
  template: 面上项目
  input_mode: from_materials
  language: zh
convergence:
  section_score_threshold: 80
  global_score_threshold: 85
  max_major_issues: 2
  max_section_rounds: 3
  max_global_rounds: 5
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
checklist_weight_map:
  critical: 3
  high: 2
  medium: 1
critical_threshold: 60
""")
    try:
        result, code = run_validate('config', path)
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


def test_config_missing_required():
    """测试缺少必填字段的 config"""
    path = write_yaml("""
project:
  type: nsfc
  template: 面上项目
  input_mode: from_materials
  language: zh
""")
    try:
        result, code = run_validate('config', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


def test_config_invalid_enum():
    """测试非法枚举值"""
    path = write_yaml("""
project:
  type: invalid_type
  template: 面上项目
  input_mode: from_materials
  language: zh
convergence:
  section_score_threshold: 80
  global_score_threshold: 85
  max_major_issues: 2
  max_section_rounds: 3
  max_global_rounds: 5
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
checklist_weight_map:
  critical: 3
  high: 2
  medium: 1
critical_threshold: 60
""")
    try:
        result, code = run_validate('config', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


def test_config_weight_sum_semantic():
    """测试 section 权重和不为 1.0"""
    path = write_yaml("""
project:
  type: nsfc
  template: 面上项目
  input_mode: from_materials
  language: zh
convergence:
  section_score_threshold: 80
  global_score_threshold: 85
  max_major_issues: 2
  max_section_rounds: 3
  max_global_rounds: 5
score_weights:
  section:
    logic: 0.50
    de_ai: 0.25
    completeness: 0.35
  global:
    consistency: 0.30
    narrative: 0.35
    feasibility: 0.20
    format: 0.15
checklist_weight_map:
  critical: 3
  high: 2
  medium: 1
critical_threshold: 60
""")
    try:
        result, code = run_validate('config', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
        error_msgs = ' '.join(e['message'] for e in result.get('errors', []))
        assert '权重' in error_msgs, f"errors 中应包含 '权重'，实际: {error_msgs}"
    finally:
        os.unlink(path)


# ======================== Scores 测试 ========================

def test_scores_valid():
    """测试合法的 scores 文件"""
    path = write_yaml("""
phase: init
global_round: 0
sections:
  introduction:
    status: pending
    current_round: 0
""")
    try:
        result, code = run_validate('scores', path)
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


def test_scores_invalid_status():
    """测试非法 status 枚举值"""
    path = write_yaml("""
phase: init
global_round: 0
sections:
  introduction:
    status: invalid_status
    current_round: 0
""")
    try:
        result, code = run_validate('scores', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


# ======================== Dependency Graph 测试 ========================

def test_dependency_graph_valid():
    """测试合法的 dependency_graph（两节无环）"""
    path = write_yaml("""
sections:
  introduction:
    depends_on: []
    priority: 1
  methods:
    depends_on:
      - introduction
    priority: 2
""")
    try:
        result, code = run_validate('dependency_graph', path)
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


def test_dependency_graph_missing_ref():
    """测试 depends_on 引用不存在的 section"""
    path = write_yaml("""
sections:
  introduction:
    depends_on:
      - nonexistent_section
    priority: 1
""")
    try:
        result, code = run_validate('dependency_graph', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


def test_dependency_graph_cycle():
    """测试有环依赖 A→B→A"""
    path = write_yaml("""
sections:
  section_a:
    depends_on:
      - section_b
    priority: 1
  section_b:
    depends_on:
      - section_a
    priority: 2
""")
    try:
        result, code = run_validate('dependency_graph', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


# ======================== Manifest 测试 ========================

def test_manifest_valid():
    """测试合法的 manifest"""
    path = write_yaml("""
materials:
  - path: materials/paper1.pdf
    type: paper
    description: 一篇关于深度学习的论文
""")
    try:
        result, code = run_validate('manifest', path)
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


def test_manifest_missing_required():
    """测试缺少 description 字段"""
    path = write_yaml("""
materials:
  - path: materials/paper1.pdf
    type: paper
""")
    try:
        result, code = run_validate('manifest', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


def test_manifest_invalid_type():
    """测试非法的 type 枚举值"""
    path = write_yaml("""
materials:
  - path: materials/paper1.pdf
    type: invalid_type
    description: 一篇关于深度学习的论文
""")
    try:
        result, code = run_validate('manifest', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


# ======================== Review Report 测试 ========================

def test_review_report_valid():
    """测试合法的 review_report（完整 frontmatter + 评分表格）"""
    content = """---
section: introduction
reviewer: R1
round: 1
dimension: logic
score: 85
has_critical_flag: false
---

## 审阅报告

| ID | Criterion | Score | Justification |
|----|-----------|-------|---------------|
| A1 | 论证逻辑 | 85 | 逻辑清晰 |

- [Major] 需要补充更多文献支撑
"""
    path = write_md(content)
    try:
        result, code = run_validate('review_report', path)
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


def test_review_report_no_frontmatter():
    """测试缺少 frontmatter 的 review_report"""
    content = """## 审阅报告

| ID | Criterion | Score | Justification |
|----|-----------|-------|---------------|
| A1 | 论证逻辑 | 85 | 逻辑清晰 |
"""
    path = write_md(content)
    try:
        result, code = run_validate('review_report', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


def test_review_report_missing_table():
    """测试有 frontmatter 但无评分表格"""
    content = """---
section: introduction
reviewer: R1
round: 1
dimension: logic
score: 85
has_critical_flag: false
---

## 审阅报告

这是一份审阅报告，但缺少评分表格。
"""
    path = write_md(content)
    try:
        result, code = run_validate('review_report', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


def test_review_report_wrong_dimension():
    """测试 R1 声称 dimension:consistency（应为 logic）"""
    content = """---
section: introduction
reviewer: R1
round: 1
dimension: consistency
score: 85
has_critical_flag: false
---

## 审阅报告

| ID | Criterion | Score | Justification |
|----|-----------|-------|---------------|
| A1 | 一致性 | 85 | 一致 |
"""
    path = write_md(content)
    try:
        result, code = run_validate('review_report', path)
        assert result['valid'] is False, f"应为 invalid，实际: {result}"
        assert code == 1
    finally:
        os.unlink(path)


# ======================== Outline 测试 ========================

def test_outline_valid():
    """测试合法的 outline（nsfc，7 个章节标题）"""
    content = """---
project_name: 测试项目
generated_by: architect
sections:
  - name: 立项依据
    core_claim: 研究意义
    target_length: 3000字
  - name: 研究内容
    core_claim: 核心内容
    target_length: 4000字
---

### 一、立项依据与研究内容

研究背景...

### 二、研究目标与研究内容

研究目标...

### 三、拟采取的研究方案及可行性分析

方案描述...

### 四、本项目的特色与创新之处

特色说明...

### 五、年度研究计划及预期研究结果

研究计划...

### 六、研究基础与工作条件

研究基础...

### 七、经费申请说明

经费说明...
"""
    path = write_md(content)
    try:
        result, code = run_validate('outline', path, extra_args=['--project-type', 'nsfc'])
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


# ======================== Claim Registry 测试 ========================

def test_claim_registry_valid():
    """测试合法的 claim_registry"""
    content = """---
claims_count: 2
generated_from: materials
last_updated: "2024-01-01"
---

## 论点注册表

| 论点ID | 核心论点 | 支撑材料 | 所属章节 |
|--------|---------|---------|---------|
| C1 | 深度学习可以提升效率 | paper1.pdf | introduction |
| C2 | 注意力机制是关键 | paper2.pdf | methods |
"""
    path = write_md(content)
    try:
        result, code = run_validate('claim_registry', path)
        assert result['valid'] is True, f"应为 valid，实际: {result}"
        assert code == 0
    finally:
        os.unlink(path)


# ======================== All 模式测试 ========================

def test_validate_all_discovers_project_root_config_and_scores():
    """测试 all 模式发现项目根目录的 config.yaml 和 scores.yaml"""
    project_dir = tempfile.mkdtemp(prefix='test_validate_all_')
    try:
        with open(os.path.join(project_dir, 'config.yaml'), 'w', encoding='utf-8') as f:
            f.write("""
project:
  type: nsfc
  template: 面上项目
  input_mode: auto
  language: zh
convergence:
  section_score_threshold: 80
  global_score_threshold: 85
  max_major_issues: 2
  max_section_rounds: 3
  max_global_rounds: 5
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
checklist_weight_map:
  critical: 3
  high: 2
  medium: 1
critical_threshold: 60
""")
        with open(os.path.join(project_dir, 'scores.yaml'), 'w', encoding='utf-8') as f:
            f.write("""
phase: init
global_round: 0
sections:
  摘要:
    status: pending
    current_round: 0
""")

        result, code = run_validate('all', project_dir)
        validated_types = {item['type'] for item in result}

        assert code == 0, f"应通过 all 校验，实际: {result}"
        assert {'config', 'scores'}.issubset(validated_types)
    finally:
        shutil.rmtree(project_dir)


# ======================== 测试运行器 ========================

if __name__ == '__main__':
    # 收集所有 test_ 开头的函数
    test_functions = [
        (name, obj) for name, obj in globals().items()
        if name.startswith('test_') and callable(obj)
    ]
    test_functions.sort(key=lambda x: x[0])

    passed = 0
    failed = 0
    failures = []

    for name, func in test_functions:
        try:
            func()
            print(f'  PASS: {name}')
            passed += 1
        except AssertionError as e:
            print(f'  FAIL: {name} - {e}')
            failed += 1
            failures.append((name, str(e)))
        except Exception as e:
            print(f'  FAIL: {name} - 异常: {e}')
            failed += 1
            failures.append((name, str(e)))

    print(f'\n总计: {passed + failed} 个测试, {passed} 通过, {failed} 失败')

    if failures:
        print('\n失败详情:')
        for name, msg in failures:
            print(f'  {name}: {msg}')

    sys.exit(1 if failed > 0 else 0)
