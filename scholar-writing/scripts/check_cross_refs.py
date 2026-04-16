#!/usr/bin/env python3
"""交叉引用检测脚本。

功能：扫描目录下所有 .md 文件，检测文件之间的交叉引用模式，包括：
     - "如前所述"、"如...所述" 等引用前序章节的表述
     - "研究内容X" 引用研究内容章节
     - "创新点X" 引用创新点章节
     - 其他章节名称出现在非本章节文件中

输入参数：
    sys.argv[1] - 包含 .md 文件的目录路径

输出返回值：
    JSON 到 stdout：{文件名: [被引用的其他文件名列表]}
    错误时：{"error": "描述"} 并退出码 1
"""
import sys
import os
import re
import json
import glob


def extract_section_name(filename):
    """从文件名中提取章节名称。

    功能：去除文件名中的序号前缀和扩展名，提取纯章节名称。
    输入参数：filename - 文件名（如 "02_立项依据.md"）
    输出返回值：章节名称字符串（如 "立项依据"）
    """
    name = os.path.splitext(filename)[0]
    # 去除数字前缀和分隔符（如 01_、02_）
    name = re.sub(r'^\d+[_\-\s]*', '', name)
    return name


def find_cross_references(files_content, filenames):
    """检测文件之间的交叉引用关系。

    功能：分析每个文件的内容，查找对其他章节的引用。
    输入参数：
        files_content - 字典 {文件名: 文件内容}
        filenames - 文件名列表
    输出返回值：字典 {文件名: [被引用的其他文件名列表]}
    """
    # 构建章节名称到文件名的映射
    section_map = {}
    for fname in filenames:
        section_name = extract_section_name(fname)
        if section_name:
            section_map[section_name] = fname

    result = {}

    for fname in filenames:
        content = files_content[fname]
        referenced_files = set()

        # 模式 1：直接引用章节名称（在非本章节文件中出现其他章节名）
        for section_name, section_file in section_map.items():
            if section_file == fname:
                continue  # 跳过自身
            if section_name in content:
                referenced_files.add(section_file)

        # 模式 2："如前所述"、"如...所述" 等 → 引用前序章节
        if re.search(r'如前所述|如上所述|前文所述|前述', content):
            # 查找排序在当前文件之前的文件
            current_idx = filenames.index(fname)
            for prev_fname in filenames[:current_idx]:
                referenced_files.add(prev_fname)

        # 模式 3："研究内容一/二/三" 或 "研究内容1/2/3" → 引用研究内容章节
        if re.search(r'研究内容[一二三四五六七八九十\d]', content):
            for section_name, section_file in section_map.items():
                if '研究内容' in section_name and section_file != fname:
                    referenced_files.add(section_file)

        # 模式 4："创新点一/二/三" 或 "创新点1/2/3" → 引用创新点相关章节
        if re.search(r'创新点[一二三四五六七八九十\d]', content):
            for section_name, section_file in section_map.items():
                if '创新' in section_name and section_file != fname:
                    referenced_files.add(section_file)

        if referenced_files:
            result[fname] = sorted(referenced_files)

    return result


def main():
    """主函数：解析命令行参数并执行交叉引用检测。"""
    if len(sys.argv) != 2:
        print(json.dumps({"error": "用法: check_cross_refs.py <目录路径>"}, ensure_ascii=False))
        sys.exit(1)

    dirpath = sys.argv[1]

    if not os.path.isdir(dirpath):
        print(json.dumps({"error": f"目录不存在: {dirpath}"}, ensure_ascii=False))
        sys.exit(1)

    md_files = sorted(glob.glob(os.path.join(dirpath, '*.md')))
    if not md_files:
        print(json.dumps({"error": "目录中没有找到 .md 文件"}, ensure_ascii=False))
        sys.exit(1)

    filenames = [os.path.basename(f) for f in md_files]
    files_content = {}
    for filepath in md_files:
        fname = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            files_content[fname] = f.read()

    result = find_cross_references(files_content, filenames)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
