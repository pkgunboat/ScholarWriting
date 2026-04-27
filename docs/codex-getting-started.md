# Codex 使用指南

推荐使用路径是先把“学术写作助手”安装到本机 Codex，再用 Codex 打开自己的写作项目。`scholar-writing` 是机器 ID、CLI 命令和安装目录名。

## 一键安装

在 Codex 里说：

```text
帮我安装这个仓库：https://github.com/<owner>/<repo>
```

本机仓库也可以这样说：

```text
帮我安装本机这个仓库：./ScholarWriting
```

Codex 会读取仓库根目录的 `SKILL.md`，然后执行 `scripts/install-codex.sh`。安装完成后重启 Codex。

如果检测到旧版 `scholar-writing` 安装，流程应停止并询问用户是否覆盖。用户确认后再执行：

```bash
bash scripts/install-codex.sh --replace
```

终端手动安装命令：

```bash
bash scripts/install-codex.sh
```

安装后重启 Codex。Codex 会发现：

```text
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/
${CODEX_HOME:-$HOME/.codex}/agents/scholar-*.toml
```

## 一键删除

在 Codex 里说：

```text
帮我卸载学术写作助手
```

或：

```text
帮我卸载本机这个仓库：./ScholarWriting
```

Codex 会按仓库根目录 `SKILL.md` 中的卸载流程执行。卸载不会删除用户自己的写作项目。

终端手动卸载命令：

```bash
bash scripts/uninstall-codex.sh
```

卸载只清理 Codex 中安装的 skill、runtime 和 agents。

## 在用户项目中使用

新建一个写作项目目录，把材料放进去：

```text
my-proposal/
├── materials/
├── planning/
└── sections/
```

用 Codex 打开这个目录，然后输入：

```text
使用学术写作助手继续处理 ./my-proposal。
```

常见触发方式：

```text
使用学术写作助手基于 ./my-proposal/materials 生成申报书大纲，并继续写作。
```

```text
使用学术写作助手审阅并优化 ./my-proposal/sections 里的初稿。
```

Codex 会调用已安装的 `scholar-writing` skill。controller 和 references 来自安装 runtime，用户项目只保存自己的材料和写作产物。

## 检查任务包与规则资料

下面的命令主要用于开发者排障。普通用户可以让 Codex 在后台执行。

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing taskpack my-proposal --format json
```

输出中的 `reference_inputs` 是本轮 agent 应读取的质量规则。它们来自 `scholar_writing/resources/references/`，包括中文学术风格、国自然结构、去 AI 痕迹规则和章节句式模板。

用户通常不需要手动打开这些文件。Codex skill 会先生成 taskpack，再把 `reference_inputs` 作为写作、审阅或修订规则传给 custom agent。

## 常用 CLI

在源码仓库中调试时可以使用：

```bash
uv run scholar-writing validate examples/from-materials --format json
uv run scholar-writing status examples/from-draft --format json
uv run scholar-writing next examples/from-outline --format json
uv run scholar-writing taskpack examples/from-outline --format json
uv run scholar-writing advance examples/from-draft --format json
```

三种入口 fixture：

- `examples/from-materials`：应返回 `run_architect`。
- `examples/from-outline`：应返回 `run_writer`。
- `examples/from-draft`：应返回 `run_reviewers`。

## 开发者调试 repo-local skill 和 agents

开发者可以直接用本仓库作为 Codex workspace 调试：

```text
.agents/skills/scholar-writing/SKILL.md
.codex/agents/*.toml
```

在 Codex 中输入：

```text
使用学术写作助手审阅优化 examples/from-draft。
```

这会走源码仓库内的平台通用 repo-local skill；在 Codex 中还会配合 `.codex/agents`，适合调试 agent 文案、taskpack、reference_inputs 和状态推进。

## 使用临时 Codex Home 调试安装器

```bash
CODEX_HOME=.codex-dev-home bash scripts/install-codex.sh --no-sync
CODEX_HOME=.codex-dev-home .codex-dev-home/skills/scholar-writing/bin/scholar-writing --help
CODEX_HOME=.codex-dev-home bash scripts/uninstall-codex.sh
```

这个流程用于验证安装产物，不会影响真实 Codex 安装。

## 在 Codex 中触发

可以直接要求：

```text
使用学术写作助手审阅优化 ./my-proposal。
```

Codex 应读取已安装的 `scholar-writing` skill，先运行 controller 获取 next action，再按需使用安装的 4 类 custom agents。

## 当前边界

- 当前安装方式是本机 Codex skill + agents，plugin 分发属于后续阶段。
- CLI 负责确定性状态判断，LLM agent 负责写作、审阅和修订。
- `reference_inputs` 负责把框架内置写作规则接入 agent handoff。
- `scores.yaml` 是状态源。
- critical 或大范围修订必须先确认。
