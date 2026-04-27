#!/usr/bin/env python3
"""字数统计脚本。

功能：统计 Markdown 文件中的中文字符数、英文单词数、总字符数和预估页数。
     支持单文件模式和目录模式。

输入参数：
    sys.argv[1] - 文件路径（单文件模式）或目录路径（目录模式）

输出返回值：
    JSON 到 stdout。
    单文件模式：{"chinese_chars": int, "english_words": int, "total_chars": int, "estimated_pages": float}
    目录模式：{文件名: {统计}, ..., "_total": {汇总统计}}
    错误时：{"error": "描述"} 并退出码 1
"""
import sys
import os
import re
import json
import glob


def strip_markdown(text):
    """去除 Markdown 标记，保留纯文本内容。

    功能：移除标题标记、强调标记、链接、图片、代码块等 Markdown 语法。
    输入参数：text - 原始 Markdown 文本
    输出返回值：去除标记后的纯文本
    """
    # 去除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    # 去除标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 去除图片和链接
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # 去除强调标记
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # 去除水平线
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # 去除列表标记
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text


def count_words(text):
    """统计文本中的中文字符数、英文单词数、总字符数和预估页数。

    功能：对去除 Markdown 标记后的文本进行字数统计。
    输入参数：text - 纯文本内容
    输出返回值：字典，包含 chinese_chars, english_words, total_chars, estimated_pages
    """
    clean = strip_markdown(text)

    # 统计中文字符（CJK 统一表意文字范围）
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', clean))

    # 统计英文单词（连续字母序列）
    english_words = len(re.findall(r'[a-zA-Z]+', clean))

    # 总字符数（去除空白后）
    total_chars = len(re.sub(r'\s', '', clean))

    # 预估页数：按每页 800 中文字符估算
    char_equivalent = chinese_chars + english_words * 2  # 英文单词平均按 2 字符当量
    estimated_pages = round(char_equivalent / 800, 2)

    return {
        "chinese_chars": chinese_chars,
        "english_words": english_words,
        "total_chars": total_chars,
        "estimated_pages": estimated_pages
    }


def count_file(filepath):
    """统计单个文件的字数。

    功能：读取文件内容并进行字数统计。
    输入参数：filepath - 文件路径
    输出返回值：字数统计字典
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return count_words(text)


def count_directory(dirpath):
    """统计目录下所有 .md 文件的字数。

    功能：遍历目录下所有 Markdown 文件，分别统计并汇总。
    输入参数：dirpath - 目录路径
    输出返回值：字典，每个文件名对应统计，加 _total 汇总
    """
    md_files = sorted(glob.glob(os.path.join(dirpath, '*.md')))
    if not md_files:
        return {"error": "目录中没有找到 .md 文件"}

    result = {}
    total = {"chinese_chars": 0, "english_words": 0, "total_chars": 0, "estimated_pages": 0}

    for filepath in md_files:
        filename = os.path.basename(filepath)
        stats = count_file(filepath)
        result[filename] = stats
        for key in total:
            total[key] += stats[key]

    total["estimated_pages"] = round(total["estimated_pages"], 2)
    result["_total"] = total
    return result


def main():
    """主函数：解析命令行参数并执行字数统计。"""
    if len(sys.argv) != 2:
        print(json.dumps({"error": "用法: count_words.py <文件路径或目录路径>"}, ensure_ascii=False))
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isfile(path):
        result = count_file(path)
    elif os.path.isdir(path):
        result = count_directory(path)
    else:
        print(json.dumps({"error": f"路径不存在: {path}"}, ensure_ascii=False))
        sys.exit(1)

    if "error" in result:
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
