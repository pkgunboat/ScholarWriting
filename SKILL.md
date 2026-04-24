---
name: scholar-writing
description: Install, uninstall, and use the ScholarWriting Codex workflow from this repository URL for academic writing, NSFC proposals, papers, draft review, and write-review-revision loops.
---

# ScholarWriting Codex Installer

Use this skill when the user provides this repository address, a local repository path, or the name "scholar writing" and asks to install, uninstall, update, or use ScholarWriting in Codex. 用户给出仓库地址、本机仓库路径，或直接说 scholar writing 并要求安装或卸载时，按本文件执行。

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

After installation, tell the user to restart Codex so the installed `scholar-writing` skill and custom agents are reloaded.

## Natural-Language Uninstall

When the user says something like:

```text
帮我卸载 scholar writing
```

or:

```text
帮我卸载本机这个仓库：./ScholarWriting
```

remove the local Codex installation:

```bash
bash scripts/uninstall-codex.sh
```

This removes only the Codex skill runtime and ScholarWriting custom agents. It does not delete the user's writing projects.

## Installed Usage

After install, users should open their own writing project in Codex, not this source repository. Then they can ask:

```text
使用 scholar-writing 继续处理 ./my-proposal。
```

or:

```text
使用 scholar-writing 审阅并优化 ./my-proposal 的申报书初稿。
```

The installed runtime provides the controller, schemas, prompts, templates, and references. The user's project stores only their materials, outline, sections, reviews, and revisions.
