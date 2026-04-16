#!/usr/bin/env python3
"""
Mermaid 图表渲染脚本

功能：将 .mmd (Mermaid) 格式文件渲染为 svg 和 png 格式。
输入：Mermaid 格式文件路径或目录
输出：JSON 格式结果，包含渲染状态和输出文件路径

依赖：需要安装 mmdc (mermaid-cli)
  npm install -g @mermaid-js/mermaid-cli

参数：
  input_path: .mmd 文件路径或包含 .mmd 文件的目录
  --output-dir: 输出目录（默认与输入文件同目录）
  --formats: 输出格式，逗号分隔（默认 svg,png）
  --theme: Mermaid 主题（default, neutral, dark, forest）
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def check_mmdc_installed():
    """
    检查 mmdc (mermaid-cli) 是否已安装。

    返回值:
        bool: True 表示已安装，False 表示未安装
    """
    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def render_mermaid_file(input_path, output_dir, formats, theme):
    """
    渲染单个 Mermaid 文件为指定格式。

    输入参数:
        input_path (str): .mmd 文件的绝对路径
        output_dir (str): 输出目录路径
        formats (list): 输出格式列表，如 ['svg', 'png']
        theme (str): Mermaid 主题名

    返回值:
        dict: 包含 status、input、outputs 和 error(如有) 的结果字典
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "input": str(input_path),
        "outputs": [],
        "status": "success",
        "error": None
    }

    for fmt in formats:
        output_file = output_dir / f"{input_path.stem}.{fmt}"
        cmd = [
            "mmdc",
            "-i", str(input_path),
            "-o", str(output_file),
            "-t", theme,
            "-b", "transparent"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                results["outputs"].append({
                    "format": fmt,
                    "path": str(output_file),
                    "size_bytes": output_file.stat().st_size if output_file.exists() else 0
                })
            else:
                results["status"] = "partial_failure"
                results["outputs"].append({
                    "format": fmt,
                    "path": str(output_file),
                    "error": result.stderr.strip()
                })
        except subprocess.TimeoutExpired:
            results["status"] = "partial_failure"
            results["outputs"].append({
                "format": fmt,
                "path": str(output_file),
                "error": "渲染超时（30秒）"
            })

    return results


def find_mermaid_files(input_path):
    """
    查找指定路径下的所有 .mmd 文件。

    输入参数:
        input_path (str): 文件路径或目录路径

    返回值:
        list: .mmd 文件的 Path 对象列表
    """
    input_path = Path(input_path)
    if input_path.is_file():
        return [input_path]
    elif input_path.is_dir():
        return sorted(input_path.glob("**/*.mmd"))
    else:
        return []


def main():
    """
    主函数：解析命令行参数并执行渲染。

    返回值:
        无（通过 stdout 输出 JSON 结果）
    """
    parser = argparse.ArgumentParser(
        description="将 Mermaid (.mmd) 文件渲染为 svg/png 格式"
    )
    parser.add_argument(
        "input_path",
        help=".mmd 文件路径或包含 .mmd 文件的目录"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="输出目录（默认与输入文件同目录）"
    )
    parser.add_argument(
        "--formats",
        default="svg,png",
        help="输出格式，逗号分隔（默认 svg,png）"
    )
    parser.add_argument(
        "--theme",
        default="neutral",
        choices=["default", "neutral", "dark", "forest"],
        help="Mermaid 主题（默认 neutral）"
    )

    args = parser.parse_args()
    formats = [f.strip() for f in args.formats.split(",")]

    # 检查 mmdc 是否安装
    if not check_mmdc_installed():
        result = {
            "status": "error",
            "error": "mmdc (mermaid-cli) 未安装。请运行: npm install -g @mermaid-js/mermaid-cli",
            "files": []
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 查找 .mmd 文件
    mmd_files = find_mermaid_files(args.input_path)
    if not mmd_files:
        result = {
            "status": "error",
            "error": f"未找到 .mmd 文件: {args.input_path}",
            "files": []
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 渲染每个文件
    all_results = []
    for mmd_file in mmd_files:
        output_dir = Path(args.output_dir) if args.output_dir else mmd_file.parent
        file_result = render_mermaid_file(mmd_file, output_dir, formats, args.theme)
        all_results.append(file_result)

    # 输出结果
    overall_status = "success"
    for r in all_results:
        if r["status"] != "success":
            overall_status = "partial_failure"
            break

    output = {
        "status": overall_status,
        "files_processed": len(all_results),
        "results": all_results
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if overall_status != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
