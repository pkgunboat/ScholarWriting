#!/usr/bin/env python3
"""Word 文档导出脚本。

功能：通过 pandoc 将目录下所有 .md 文件按文件名排序合并，导出为 .docx 格式。

输入参数：
    sys.argv[1] - 包含 .md 文件的 sections 目录路径
    sys.argv[2] - 输出 .docx 文件路径

输出返回值：
    JSON 到 stdout：{"output": "输出文件路径", "files_merged": int}
    错误时：{"error": "描述"} 并退出码 1
"""
import sys
import os
import json
import glob
import subprocess


def merge_and_export(dirpath, output_path):
    """合并目录下的 Markdown 文件并通过 pandoc 导出为 docx。

    功能：按文件名排序读取所有 .md 文件，合并后调用 pandoc 转换为 Word 文档。
    输入参数：
        dirpath - 包含 .md 文件的目录路径
        output_path - 输出 .docx 文件的路径
    输出返回值：合并的文件数量
    """
    md_files = sorted(glob.glob(os.path.join(dirpath, '*.md')))
    if not md_files:
        print(json.dumps({"error": "目录中没有找到 .md 文件"}, ensure_ascii=False))
        sys.exit(1)

    # 合并所有 Markdown 文件内容
    merged_content = []
    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            merged_content.append(f.read())

    combined = '\n\n'.join(merged_content)

    # 调用 pandoc 转换
    try:
        proc = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', 'docx', '-o', output_path],
            input=combined,
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            print(json.dumps({"error": f"pandoc 转换失败: {proc.stderr.strip()}"}, ensure_ascii=False))
            sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({"error": "pandoc 未安装，请先安装 pandoc"}, ensure_ascii=False))
        sys.exit(1)

    return len(md_files)


def main():
    """主函数：解析命令行参数并执行导出。"""
    if len(sys.argv) != 3:
        print(json.dumps({"error": "用法: export_docx.py <sections目录> <输出文件路径>"}, ensure_ascii=False))
        sys.exit(1)

    dirpath = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.isdir(dirpath):
        print(json.dumps({"error": f"目录不存在: {dirpath}"}, ensure_ascii=False))
        sys.exit(1)

    files_count = merge_and_export(dirpath, output_path)

    result = {
        "output": output_path,
        "files_merged": files_count
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
