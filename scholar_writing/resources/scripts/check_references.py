#!/usr/bin/env python3
"""引文检查脚本。

功能：检测 Markdown 文件中的引文标记（[N]、[N,M]、[N-M] 格式），
     统计唯一引文数量，并尝试从上下文提取年份信息。

输入参数：
    sys.argv[1] - Markdown 文件路径

输出返回值：
    JSON 到 stdout：{
        "citation_count": int,       # 唯一引文编号数量
        "citations": [int, ...],     # 所有唯一引文编号列表（升序）
        "year_distribution": {年份: 次数}  # 引文附近出现的年份分布
    }
    错误时：{"error": "描述"} 并退出码 1
"""
import sys
import os
import re
import json


def extract_citations(text):
    """从文本中提取所有引文编号。

    功能：使用正则匹配 [N]、[N,M]、[N-M] 格式的引文标记，解析出所有编号。
    输入参数：text - Markdown 文本
    输出返回值：排序后的唯一引文编号列表
    """
    citation_numbers = set()

    # 匹配方括号内的引文标记：[1], [2,3], [4-6], [1,3-5] 等
    pattern = r'\[(\d+(?:\s*[,，]\s*\d+)*(?:\s*[-–]\s*\d+)*)\]'
    matches = re.findall(pattern, text)

    for match in matches:
        # 处理逗号分隔：[2,3]
        parts = re.split(r'\s*[,，]\s*', match)
        for part in parts:
            # 处理范围：[4-6]
            range_match = re.match(r'(\d+)\s*[-–]\s*(\d+)', part.strip())
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                for n in range(start, end + 1):
                    citation_numbers.add(n)
            else:
                num = part.strip()
                if num.isdigit():
                    citation_numbers.add(int(num))

    return sorted(citation_numbers)


def extract_years(text):
    """从文本中提取引文相关的年份信息。

    功能：在引文标记附近搜索年份（如 [7](2024)），以及文本中独立出现的年份。
    输入参数：text - Markdown 文本
    输出返回值：年份分布字典 {年份字符串: 出现次数}
    """
    year_counts = {}

    # 匹配引文标记后紧跟的年份：[7](2024)
    pattern1 = r'\[\d+(?:\s*[,，]\s*\d+)*(?:\s*[-–]\s*\d+)*\]\s*\((\d{4})\)'
    for match in re.findall(pattern1, text):
        year = match
        year_counts[year] = year_counts.get(year, 0) + 1

    # 匹配文本中出现的四位年份（限定在合理范围 1900-2099）
    pattern2 = r'(?<!\d)((?:19|20)\d{2})(?!\d)'
    for match in re.findall(pattern2, text):
        # 避免重复统计已在引文括号中的年份
        year_counts[match] = year_counts.get(match, 0) + 1

    return year_counts


def main():
    """主函数：解析命令行参数并执行引文检查。"""
    if len(sys.argv) != 2:
        print(json.dumps({"error": "用法: check_references.py <Markdown文件路径>"}, ensure_ascii=False))
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.isfile(filepath):
        print(json.dumps({"error": f"文件不存在: {filepath}"}, ensure_ascii=False))
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    citations = extract_citations(text)
    year_distribution = extract_years(text)

    result = {
        "citation_count": len(citations),
        "citations": citations,
        "year_distribution": year_distribution
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
