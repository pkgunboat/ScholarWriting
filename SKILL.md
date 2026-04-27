---
name: scholar-writing
description: 安装、卸载和使用“学术写作助手”的 Codex 版本，用于国自然申报书、论文、初稿审阅和写作-审阅-修订循环。
---

# 学术写作助手 Codex 安装器

本安装入口的机器 ID 是 `scholar-writing`。面向中文用户时，优先称为“学术写作助手”。

用户给出仓库地址、本机仓库路径，或直接说“学术写作助手”“scholar writing”并要求安装、卸载、更新或使用时，按本文件执行。

## Natural-Language Install

When the user says something like:

```text
帮我安装这个仓库：https://github.com/<owner>/<repo>
```

or:

```text
帮我安装本机这个仓库：./ScholarWriting
```

install ScholarWriting by running the repository installer:

```bash
bash scripts/install-codex.sh
```

If the installer reports an existing ScholarWriting installation, stop and ask the user whether to replace the old installation. Only after explicit confirmation, rerun:

```bash
bash scripts/install-codex.sh --replace
```

安装后，告诉用户重启 Codex，让已安装的“学术写作助手”（机器 ID：`scholar-writing`）和 custom agents 重新加载。

## Natural-Language Uninstall

When the user says something like:

```text
帮我卸载学术写作助手
```

or:

```text
帮我卸载本机这个仓库：./ScholarWriting
```

remove the local Codex installation:

```bash
bash scripts/uninstall-codex.sh
```

这只会删除 Codex 中安装的 skill runtime 和 ScholarWriting custom agents，不会删除用户自己的写作项目。

## Installed Usage

After install, users should open their own writing project in Codex, not this source repository. Then they can ask:

```text
使用学术写作助手继续处理 ./my-proposal。
```

or:

```text
使用学术写作助手审阅并优化 ./my-proposal 的申报书初稿。
```

The installed runtime provides the controller, schemas, prompts, templates, and references. The user's project stores only their materials, outline, sections, reviews, and revisions.
