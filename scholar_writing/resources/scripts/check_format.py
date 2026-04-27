#!/usr/bin/env python3
"""Markdown 格式检查脚本。

功能：检查 Markdown 文件的标题层级结构，发现格式问题（如标题跳级、缺少一级标题等）。

输入参数：
    sys.argv[1] - Markdown 文件路径

输出返回值：
    JSON 到 stdout：{"heading_structure": [...], "issues": [...]}
    heading_structure 每项：{"level": int, "text": str, "line": int}
    issues 每项：问题描述字符串
    错误时：{"error": "描述"} 并退出码 1
"""
import sys
import os
import re
import json


def extract_headings(text):
    """从 Markdown 文本中提取所有标题。

    功能：使用正则匹配 ATX 风格的 Markdown 标题。
    输入参数：text - Markdown 文本
    输出返回值：标题列表，每项为 {"level": int, "text": str, "line": int}
    """
    headings = []
    for i, line in enumerate(text.split('\n'), 1):
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append({
                "level": level,
                "text": heading_text,
                "line": i
            })
    return headings


def check_issues(headings):
    """检查标题结构中的格式问题。

    功能：检测常见的标题格式问题，如缺少一级标题、标题跳级等。
    输入参数：headings - 标题列表
    输出返回值：问题描述字符串列表
    """
    issues = []

    if not headings:
        issues.append("文件中没有找到任何标题")
        return issues

    # 检查是否缺少一级标题
    levels = [h["level"] for h in headings]
    if 1 not in levels:
        issues.append("缺少一级标题（# 标题）")

    # 检查标题跳级（如从 # 直接到 ###）
    for i in range(1, len(headings)):
        prev_level = headings[i - 1]["level"]
        curr_level = headings[i]["level"]
        if curr_level > prev_level + 1:
            prev_marks = '#' * prev_level
            curr_marks = '#' * curr_level
            line_num = headings[i]['line']
            heading_text = headings[i]['text']
            issues.append(
                f"第 {line_num} 行标题跳级：从 {prev_marks} 跳到 {curr_marks}（\u201c{heading_text}\u201d）"
            )

    # 检查是否有重复的一级标题
    h1_headings = [h for h in headings if h["level"] == 1]
    if len(h1_headings) > 1:
        issues.append(f"存在多个一级标题（共 {len(h1_headings)} 个），建议每个文件只有一个一级标题")

    return issues


def main():
    """主函数：解析命令行参数并执行格式检查。"""
    if len(sys.argv) != 2:
        print(json.dumps({"error": "用法: check_format.py <Markdown文件路径>"}, ensure_ascii=False))
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.isfile(filepath):
        print(json.dumps({"error": f"文件不存在: {filepath}"}, ensure_ascii=False))
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    headings = extract_headings(text)
    issues = check_issues(headings)

    result = {
        "heading_structure": headings,
        "issues": issues
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
