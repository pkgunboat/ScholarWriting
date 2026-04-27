#!/usr/bin/env python3
"""辅助脚本测试套件。"""
from pathlib import Path
import subprocess, json, tempfile, os, shutil, sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / 'scholar_writing' / 'resources' / 'scripts'

def run_script(script, *args):
    """运行脚本并返回解析后的 JSON 输出。"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script)] + list(args),
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    return json.loads(result.stdout), result.returncode

def test_count_words_file():
    """测试单文件字数统计。"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("# 标题\n\n这是一段测试文本，包含中文和English混合内容。\n\n## 二级标题\n\n更多内容在这里。")
        tmp = f.name
    try:
        data, code = run_script('count_words.py', tmp)
        assert code == 0, f"Exit code: {code}"
        assert 'chinese_chars' in data, "Missing chinese_chars"
        assert 'english_words' in data, "Missing english_words"
        assert 'total_chars' in data, "Missing total_chars"
        assert 'estimated_pages' in data, "Missing estimated_pages"
        assert data['chinese_chars'] > 0, f"chinese_chars={data['chinese_chars']}"
        assert data['english_words'] > 0, f"english_words={data['english_words']}"
    finally:
        os.unlink(tmp)

def test_count_words_dir():
    """测试目录字数统计。"""
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, '01_摘要.md'), 'w', encoding='utf-8') as f:
            f.write("这是摘要内容，测试用。")
        with open(os.path.join(d, '02_立项依据.md'), 'w', encoding='utf-8') as f:
            f.write("这是立项依据内容，包含更多文字用于测试字数统计功能。")
        data, code = run_script('count_words.py', d)
        assert code == 0
        assert '_total' in data, "Missing _total"
        assert data['_total']['chinese_chars'] > 0
    finally:
        shutil.rmtree(d)

def test_check_format():
    """测试格式检查。"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("# 一、立项依据\n\n## （一）研究现状\n\n内容...\n\n## （二）科学问题\n\n内容...")
        tmp = f.name
    try:
        data, code = run_script('check_format.py', tmp)
        assert code == 0
        assert 'heading_structure' in data, "Missing heading_structure"
        assert 'issues' in data, "Missing issues"
        assert isinstance(data['heading_structure'], list)
        assert isinstance(data['issues'], list)
    finally:
        os.unlink(tmp)

def test_check_references():
    """测试引文检查。"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("研究表明[1]，该方法有效[2,3]。近年来[4-6]的工作进一步证实了这一点。参考文献[7](2024)和[8](2022)。")
        tmp = f.name
    try:
        data, code = run_script('check_references.py', tmp)
        assert code == 0
        assert 'citation_count' in data, "Missing citation_count"
        assert data['citation_count'] > 0, f"citation_count={data['citation_count']}"
    finally:
        os.unlink(tmp)

def test_check_cross_refs():
    """测试交叉引用检测。"""
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, '02_立项依据.md'), 'w', encoding='utf-8') as f:
            f.write("如研究内容所述，本项目拟开展相关研究。")
        with open(os.path.join(d, '03_研究内容.md'), 'w', encoding='utf-8') as f:
            f.write("研究内容一：基于强化学习的GUI Agent方法。")
        with open(os.path.join(d, '04_研究方案.md'), 'w', encoding='utf-8') as f:
            f.write("针对研究内容一，本项目提出如下方案。创新点在于...")
        data, code = run_script('check_cross_refs.py', d)
        assert code == 0
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
    finally:
        shutil.rmtree(d)

def test_export_docx():
    """测试 Word 导出（需要 pandoc）。"""
    d = tempfile.mkdtemp()
    out = os.path.join(d, 'output.docx')
    try:
        with open(os.path.join(d, '01_摘要.md'), 'w', encoding='utf-8') as f:
            f.write("# 摘要\n\n这是一段测试摘要。")
        # 检查 pandoc 是否可用
        pandoc_check = subprocess.run(['which', 'pandoc'], capture_output=True)
        if pandoc_check.returncode != 0:
            print("SKIP test_export_docx: pandoc not installed")
            return
        data, code = run_script('export_docx.py', d, out)
        assert code == 0
        assert os.path.exists(out), "Output file not created"
    finally:
        shutil.rmtree(d)

if __name__ == '__main__':
    tests = [
        test_count_words_file,
        test_count_words_dir,
        test_check_format,
        test_check_references,
        test_check_cross_refs,
        test_export_docx,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f'PASSED: {t.__name__}')
            passed += 1
        except Exception as e:
            print(f'FAILED: {t.__name__}: {e}')
            failed += 1
    print(f'\n{passed} passed, {failed} failed')
