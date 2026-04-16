#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一校验脚本 validate.py
对 ScholarWriting 项目的各类配置文件、数据文件和 Markdown 文件进行 Schema 校验与语义校验。

功能：
  - 支持 config, manifest, scores, dependency_graph, outline, claim_registry, review_report 七种数据类型
  - JSON Schema 校验 + 语义规则校验 + Markdown 正文正则校验
  - 提供 CLI 接口，支持单文件和批量校验

输入参数：
  <type>: 数据类型 或 "all"
  <file>: 文件路径 或 项目根目录(all模式)
  --format: 输出格式 json|text
  --strict: 严格模式，warning 升级为 error
  --quiet: 静默模式，仅输出错误
  --project-type: 项目类型 nsfc|paper

输出：
  校验结果（错误列表、警告列表、是否通过）
"""

import argparse
import glob as glob_mod
import json
import re
import sys
from collections import deque
from pathlib import Path

import yaml

try:
    from jsonschema import Draft7Validator
except ImportError:
    from jsonschema import Draft4Validator as Draft7Validator

# Schema 文件目录
SCHEMA_DIR = Path(__file__).parent.parent / 'schemas'

# Markdown 类型（需要解析 frontmatter 的文件类型）
MARKDOWN_TYPES = {'outline', 'claim_registry', 'review_report'}

# all 模式下的文件发现规则
FILE_DISCOVERY = {
    'config': 'config/default_config.yaml',
    'scores': 'state/scores.yaml',
    'dependency_graph': 'planning/dependency_graph.yaml',
    'manifest': 'materials/manifest.yaml',
    'outline': 'planning/outline.md',
    'claim_registry': 'planning/claim_registry.md',
}

# Reviewer-Dimension 合法映射
REVIEWER_DIMENSION_MAP = {
    'R1': 'logic',
    'R2': 'de_ai',
    'R3': 'completeness',
    'R4': 'consistency',
    'R5': 'narrative',
    'R6': 'feasibility',
    'R7': 'format',
}


class ValidationResult:
    """
    校验结果容器。

    属性：
      file_path: 被校验文件路径
      data_type: 数据类型
      errors: 错误列表，每项为 dict(level, message, path?)
      warnings: 警告列表，格式同 errors
    """

    def __init__(self, file_path, data_type):
        self.file_path = str(file_path)
        self.data_type = data_type
        self.errors = []
        self.warnings = []

    @property
    def valid(self):
        """无 error 则视为通过"""
        return len(self.errors) == 0

    def add_error(self, message, path=None):
        """添加一条错误"""
        entry = {'level': 'error', 'message': message}
        if path:
            entry['path'] = path
        self.errors.append(entry)

    def add_warning(self, message, path=None):
        """添加一条警告"""
        entry = {'level': 'warning', 'message': message}
        if path:
            entry['path'] = path
        self.warnings.append(entry)

    def to_dict(self):
        """
        转换为字典格式。

        返回值：
          dict: 包含 file, type, valid, errors, warnings
        """
        return {
            'file': self.file_path,
            'type': self.data_type,
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
        }


def load_schema(data_type):
    """
    从 SCHEMA_DIR 加载指定数据类型的 Schema YAML。

    输入参数：
      data_type: str - 数据类型名称

    输出返回值：
      dict - 解析后的 Schema 字典

    异常：
      FileNotFoundError - Schema 文件不存在
    """
    schema_path = SCHEMA_DIR / f'{data_type}.schema.yaml'
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def parse_frontmatter(content):
    """
    分离 Markdown frontmatter 和正文。

    输入参数：
      content: str - 文件全部内容

    输出返回值：
      tuple(dict|None, str) - (frontmatter字典或None, 正文字符串)
    """
    # 匹配 --- 开头的 frontmatter 块
    pattern = r'^---\s*\n(.*?)\n---\s*\n?(.*)'
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return None, content
    fm_text = match.group(1)
    body = match.group(2)
    try:
        fm_data = yaml.safe_load(fm_text)
        if not isinstance(fm_data, dict):
            return None, content
        return fm_data, body
    except yaml.YAMLError:
        return None, content


def validate_schema(data, data_type, result):
    """
    使用 JSON Schema 校验数据。

    输入参数：
      data: dict - 待校验数据
      data_type: str - 数据类型
      result: ValidationResult - 校验结果容器

    输出返回值：
      无（错误写入 result）
    """
    try:
        schema = load_schema(data_type)
    except FileNotFoundError:
        result.add_error(f'Schema 文件未找到: {data_type}.schema.yaml')
        return

    validator = Draft7Validator(schema)
    for error in validator.iter_errors(data):
        path = '.'.join(str(p) for p in error.absolute_path) if error.absolute_path else ''
        result.add_error(f'Schema 校验失败: {error.message}', path=path or None)


# ======================== 语义校验器 ========================

def validate_config_semantic(data, result, **kwargs):
    """
    config 语义校验：权重求和、阈值一致性。

    输入参数：
      data: dict - config 数据
      result: ValidationResult - 校验结果容器

    校验规则：
      - section 权重和 = 1.0（容差 0.01），否则 error
      - global 权重和 = 1.0（容差 0.01），否则 error
      - section_score_threshold > global_score_threshold 时 warning
    """
    weights = data.get('score_weights', {})

    # section 权重和
    section_w = weights.get('section', {})
    if section_w:
        s = sum(v for v in section_w.values() if isinstance(v, (int, float)))
        if abs(s - 1.0) > 0.01:
            result.add_error(f'section 权重和为 {s:.4f}，应为 1.0（容差 0.01）')

    # global 权重和
    global_w = weights.get('global', {})
    if global_w:
        s = sum(v for v in global_w.values() if isinstance(v, (int, float)))
        if abs(s - 1.0) > 0.01:
            result.add_error(f'global 权重和为 {s:.4f}，应为 1.0（容差 0.01）')

    # 阈值一致性
    conv = data.get('convergence', {})
    sec_th = conv.get('section_score_threshold', 0)
    glo_th = conv.get('global_score_threshold', 0)
    if sec_th > glo_th:
        result.add_warning(
            f'section_score_threshold({sec_th}) > global_score_threshold({glo_th})，'
            '这可能导致章节已通过但全局仍不收敛'
        )


def validate_scores_semantic(data, result, **kwargs):
    """
    scores 语义校验：完成态检查、轮次上限检查。

    输入参数：
      data: dict - scores 数据
      result: ValidationResult - 校验结果容器
      kwargs: config(可选) - 用于获取 max_section_rounds

    校验规则：
      - phase=completed 时，所有 section 应为 approved
      - current_round 不超过 max_section_rounds（需 config）
    """
    phase = data.get('phase', '')
    sections = data.get('sections', {})

    if phase == 'completed':
        for sec_name, sec_data in sections.items():
            status = sec_data.get('status', '')
            if status != 'approved':
                result.add_error(
                    f'phase=completed 但 section "{sec_name}" 状态为 "{status}"，应为 approved'
                )

    config = kwargs.get('config')
    if config:
        max_rounds = config.get('convergence', {}).get('max_section_rounds', 999)
        for sec_name, sec_data in sections.items():
            cr = sec_data.get('current_round', 0)
            if cr > max_rounds:
                result.add_warning(
                    f'section "{sec_name}" current_round={cr} 超过 max_section_rounds={max_rounds}'
                )


def validate_dependency_graph_semantic(data, result, **kwargs):
    """
    dependency_graph 语义校验：引用存在性、DAG 无环、priority 一致性。

    输入参数：
      data: dict - dependency_graph 数据
      result: ValidationResult - 校验结果容器
      kwargs: template_path(可选) - 模板文件路径用于交叉校验

    校验规则：
      - depends_on 中引用的 section 必须存在于 sections 中
      - 不能存在环（使用 Kahn 算法）
      - 被依赖的节点 priority 应 <= 依赖者（否则 warning）
    """
    sections = data.get('sections', {})
    all_names = set(sections.keys())

    # 引用存在性
    for sec_name, sec_data in sections.items():
        deps = sec_data.get('depends_on', [])
        for dep in deps:
            if dep not in all_names:
                result.add_error(f'section "{sec_name}" 依赖的 "{dep}" 不存在于 sections 中')

    # DAG 无环检测（Kahn 算法）
    in_degree = {name: 0 for name in all_names}
    adj = {name: [] for name in all_names}
    for sec_name, sec_data in sections.items():
        for dep in sec_data.get('depends_on', []):
            if dep in all_names:
                adj[dep].append(sec_name)
                in_degree[sec_name] += 1

    queue = deque([n for n in all_names if in_degree[n] == 0])
    visited_count = 0
    while queue:
        node = queue.popleft()
        visited_count += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count < len(all_names):
        result.add_error('dependency_graph 中存在循环依赖')

    # priority 一致性
    for sec_name, sec_data in sections.items():
        sec_priority = sec_data.get('priority', 0)
        for dep in sec_data.get('depends_on', []):
            if dep in sections:
                dep_priority = sections[dep].get('priority', 0)
                if dep_priority > sec_priority:
                    result.add_warning(
                        f'section "{dep}"(priority={dep_priority}) 被 "{sec_name}"'
                        f'(priority={sec_priority}) 依赖，但 priority 更高'
                    )

    # 模板交叉校验
    template_path = kwargs.get('template_path')
    if template_path and Path(template_path).exists():
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = yaml.safe_load(f)
            if isinstance(template, dict):
                template_sections = set()
                # 尝试从模板中提取 section 名称
                for key in template:
                    if isinstance(template[key], dict):
                        template_sections.add(key)
                if template_sections:
                    missing = template_sections - all_names
                    extra = all_names - template_sections
                    if missing:
                        result.add_warning(f'模板中存在但 dependency_graph 缺少的 section: {missing}')
                    if extra:
                        result.add_warning(f'dependency_graph 中多出模板未定义的 section: {extra}')
        except Exception:
            pass


def validate_manifest_semantic(data, result, **kwargs):
    """
    manifest 语义校验：文件存在性检查。

    输入参数：
      data: dict - manifest 数据
      result: ValidationResult - 校验结果容器
      kwargs: base_dir(可选) - 项目根目录，用于检查 path 是否存在
    """
    base_dir = kwargs.get('base_dir')
    if not base_dir:
        return

    materials = data.get('materials', [])
    for item in materials:
        path = item.get('path', '')
        if path:
            full_path = Path(base_dir) / path
            if not full_path.exists():
                result.add_warning(f'manifest 中声明的文件不存在: {path}')


def validate_review_report_semantic(data, result, **kwargs):
    """
    review_report 语义校验：reviewer-dimension 合法组合检查。

    输入参数：
      data: dict - review_report frontmatter 数据
      result: ValidationResult - 校验结果容器

    校验规则：
      - reviewer 与 dimension 必须匹配 REVIEWER_DIMENSION_MAP
    """
    reviewer = data.get('reviewer', '')
    dimension = data.get('dimension', '')
    if reviewer and dimension:
        expected = REVIEWER_DIMENSION_MAP.get(reviewer)
        if expected and dimension != expected:
            result.add_error(
                f'reviewer "{reviewer}" 应对应 dimension "{expected}"，'
                f'但实际为 "{dimension}"'
            )


# 语义校验分发表
SEMANTIC_VALIDATORS = {
    'config': validate_config_semantic,
    'scores': validate_scores_semantic,
    'dependency_graph': validate_dependency_graph_semantic,
    'manifest': validate_manifest_semantic,
    'review_report': validate_review_report_semantic,
}


def validate_markdown_body(body, data_type, result, project_type=None):
    """
    使用 markdown_rules.yaml 中的正则规则校验 Markdown 正文。

    输入参数：
      body: str - Markdown 正文
      data_type: str - 数据类型
      result: ValidationResult - 校验结果容器
      project_type: str|None - 项目类型（nsfc|paper）
    """
    rules_path = SCHEMA_DIR / 'markdown_rules.yaml'
    if not rules_path.exists():
        return

    with open(rules_path, 'r', encoding='utf-8') as f:
        all_rules = yaml.safe_load(f)

    type_rules = all_rules.get(data_type, {})
    if not type_rules:
        return

    required_patterns = type_rules.get('required_patterns', [])
    for rule in required_patterns:
        # 检查 applies_to 过滤
        applies_to = rule.get('applies_to')
        if applies_to and project_type and project_type not in applies_to:
            continue
        if applies_to and not project_type:
            continue

        pattern = rule.get('pattern', '')
        name = rule.get('name', '')
        min_count = rule.get('min_count', 1)
        description = rule.get('description', '')

        matches = re.findall(pattern, body, re.MULTILINE)
        count = len(matches)

        if count < min_count:
            result.add_error(
                f'Markdown 正文校验失败: "{name}" 要求至少 {min_count} 处匹配，'
                f'实际找到 {count} 处。{description}'
            )

    # 评分范围校验（review_report 专用）
    score_validation = type_rules.get('score_validation')
    if score_validation:
        pattern = score_validation.get('pattern', '')
        score_range = score_validation.get('score_range', [0, 100])
        for match in re.finditer(pattern, body, re.MULTILINE):
            try:
                score = int(match.group(2))
                if score < score_range[0] or score > score_range[1]:
                    result.add_error(
                        f'评分 {match.group(1)} 的分数 {score} 超出范围 {score_range}'
                    )
            except (ValueError, IndexError):
                pass


def validate_file(data_type, file_path, base_dir=None, project_type=None, **kwargs):
    """
    统一校验入口：校验单个文件。

    输入参数：
      data_type: str - 数据类型
      file_path: str|Path - 文件路径
      base_dir: str|Path|None - 项目根目录（manifest 用）
      project_type: str|None - 项目类型
      **kwargs: 传递给语义校验器的额外参数

    输出返回值：
      ValidationResult - 校验结果
    """
    file_path = Path(file_path)
    result = ValidationResult(file_path, data_type)

    if not file_path.exists():
        result.add_error(f'文件不存在: {file_path}')
        return result

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result.add_error(f'文件读取失败: {e}')
        return result

    if data_type in MARKDOWN_TYPES:
        # Markdown 文件：分离 frontmatter
        fm_data, body = parse_frontmatter(content)

        if fm_data is None:
            result.add_error('Markdown 文件缺少有效的 YAML frontmatter')
            # 降级：仍执行正文校验
            validate_markdown_body(body, data_type, result, project_type=project_type)
            return result

        # Schema 校验 frontmatter
        validate_schema(fm_data, data_type, result)

        # 语义校验
        validator_fn = SEMANTIC_VALIDATORS.get(data_type)
        if validator_fn:
            validator_fn(fm_data, result, **kwargs)

        # 正文正则校验
        validate_markdown_body(body, data_type, result, project_type=project_type)
    else:
        # YAML 文件
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            result.add_error(f'YAML 解析失败: {e}')
            return result

        if not isinstance(data, dict):
            result.add_error('YAML 文件顶层必须为 object')
            return result

        # Schema 校验
        validate_schema(data, data_type, result)

        # 语义校验
        validator_fn = SEMANTIC_VALIDATORS.get(data_type)
        if validator_fn:
            if base_dir:
                kwargs['base_dir'] = base_dir
            validator_fn(data, result, **kwargs)

    return result


def validate_all(project_root):
    """
    批量校验项目根目录下所有已知文件。

    输入参数：
      project_root: str|Path - 项目根目录

    输出返回值：
      list[ValidationResult] - 所有校验结果
    """
    project_root = Path(project_root)
    results = []

    # 读取 config 获取 project_type 和 input_mode
    config_path = project_root / FILE_DISCOVERY['config']
    project_type = None
    config_data = None
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            project_type = config_data.get('project', {}).get('type')
        except Exception:
            pass

    # 逐类型校验
    for dtype, rel_path in FILE_DISCOVERY.items():
        fpath = project_root / rel_path
        if fpath.exists():
            kwargs = {}
            if dtype == 'manifest':
                kwargs['base_dir'] = str(project_root)
            if dtype == 'scores' and config_data:
                kwargs['config'] = config_data
            r = validate_file(dtype, fpath, project_type=project_type, **kwargs)
            results.append(r)

    # review_report: glob 查找
    review_pattern = str(project_root / 'reviews' / '**' / '*_R*.md')
    for rpath in glob_mod.glob(review_pattern, recursive=True):
        r = validate_file('review_report', rpath, project_type=project_type)
        results.append(r)

    return results


def format_text(result, quiet=False):
    """
    将 ValidationResult 格式化为人类可读文本。

    输入参数：
      result: ValidationResult - 校验结果
      quiet: bool - 静默模式仅输出错误

    输出返回值：
      str - 格式化文本
    """
    lines = []
    status = 'PASS' if result.valid else 'FAIL'
    lines.append(f'[{status}] {result.data_type}: {result.file_path}')

    for err in result.errors:
        path_info = f' ({err["path"]})' if err.get('path') else ''
        lines.append(f'  ERROR: {err["message"]}{path_info}')

    if not quiet:
        for warn in result.warnings:
            path_info = f' ({warn["path"]})' if warn.get('path') else ''
            lines.append(f'  WARNING: {warn["message"]}{path_info}')

    return '\n'.join(lines)


def main():
    """
    CLI 入口函数。

    用法：
      python validate.py <type> <file> [--format json|text] [--strict] [--quiet] [--project-type nsfc|paper]
      python validate.py all <project_root> [--format json|text] [--strict] [--quiet]
    """
    parser = argparse.ArgumentParser(description='ScholarWriting 统一校验脚本')
    parser.add_argument('type', help='数据类型或 "all"')
    parser.add_argument('file', help='文件路径或项目根目录')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='输出格式')
    parser.add_argument('--strict', action='store_true', help='严格模式：warning 升级为 error')
    parser.add_argument('--quiet', action='store_true', help='静默模式：仅输出错误')
    parser.add_argument('--project-type', choices=['nsfc', 'paper'], default=None, help='项目类型')

    args = parser.parse_args()

    if args.type == 'all':
        results = validate_all(args.file)
    else:
        results = [validate_file(args.type, args.file, project_type=args.project_type)]

    # strict 模式：warning 升级为 error
    if args.strict:
        for r in results:
            for w in r.warnings:
                w['level'] = 'error'
                r.errors.append(w)
            r.warnings = []

    # 输出
    has_error = False
    if args.format == 'json':
        if len(results) == 1:
            output = results[0].to_dict()
        else:
            output = [r.to_dict() for r in results]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        has_error = any(not r.valid for r in results)
    else:
        for r in results:
            print(format_text(r, quiet=args.quiet))
            if not r.valid:
                has_error = True

    sys.exit(1 if has_error else 0)


if __name__ == '__main__':
    main()
