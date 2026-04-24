#!/usr/bin/env bash
set -euo pipefail

sync_runtime=1
replace_existing=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-sync)
      sync_runtime=0
      shift
      ;;
    --replace)
      replace_existing=1
      shift
      ;;
    --help|-h)
      cat <<'EOF'
Usage: scripts/install-codex.sh [--no-sync] [--replace]

Install ScholarWriting into the local Codex home.

Options:
  --replace  Replace an existing ScholarWriting Codex installation. Use only after user confirmation.

Environment:
  CODEX_HOME                  Defaults to $HOME/.codex
  SCHOLAR_WRITING_INSTALL_DIR Defaults to $CODEX_HOME/skills/scholar-writing
  SCHOLAR_WRITING_AGENTS_DIR  Defaults to $CODEX_HOME/agents
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
install_dir="${SCHOLAR_WRITING_INSTALL_DIR:-$codex_home/skills/scholar-writing}"
agents_dir="${SCHOLAR_WRITING_AGENTS_DIR:-$codex_home/agents}"
runtime_dir="$install_dir/runtime"
stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/scholar-writing-install.XXXXXX")"
trap 'rm -rf "$stage_dir"' EXIT
stage_source="$stage_dir/source"

if [ -z "$install_dir" ] || [ "$install_dir" = "/" ]; then
  echo "Refusing unsafe install directory: $install_dir" >&2
  exit 1
fi

if [ -e "$install_dir" ] && [ "$replace_existing" -ne 1 ] && [ "$(cd "$install_dir" && pwd)" != "$repo_root" ]; then
  echo "Existing ScholarWriting installation detected: $install_dir" >&2
  echo "Stop and ask the user before replacing it. If they confirm, rerun with --replace." >&2
  exit 10
fi

mkdir -p "$stage_source"
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.playwright-cli' \
    --exclude '.DS_Store' \
    "$repo_root/" "$stage_source/"
else
  tar -C "$repo_root" \
    --exclude './.git' \
    --exclude './.venv' \
    --exclude './__pycache__' \
    --exclude './.pytest_cache' \
    --exclude './.playwright-cli' \
    -cf - . | tar -C "$stage_source" -xf -
fi

rm -rf "$install_dir"
mkdir -p "$install_dir" "$agents_dir" "$install_dir/bin"
mkdir -p "$runtime_dir"

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.playwright-cli' \
    --exclude '.DS_Store' \
    "$stage_source/" "$runtime_dir/"
else
  tar -C "$stage_source" \
    --exclude './.git' \
    --exclude './.venv' \
    --exclude './__pycache__' \
    --exclude './.pytest_cache' \
    --exclude './.playwright-cli' \
    -cf - . | tar -C "$runtime_dir" -xf -
fi

cat > "$install_dir/SKILL.md" <<'EOF'
---
name: scholar-writing
description: Multi-agent academic writing workflow for NSFC proposals, papers, draft review, and write-review-revision optimization loops.
---

# ScholarWriting for Codex

Use this skill when the user asks for academic writing, NSFC/国自然 proposals, proposal drafting, paper drafting, draft review, or iterative writing optimization.

## Installed Runtime

This skill is installed with a runtime directory next to this file:

```text
runtime/
bin/scholar-writing
```

Use `bin/scholar-writing` for controller commands. The wrapper sets `SCHOLAR_WRITING_RUNTIME` so the controller can find schemas, references, prompts, and templates while the current working directory remains the user's writing project.

## User Workflow

Users normally work in their own project directory, not inside the ScholarWriting source repository.

Expected project layout:

```text
my-proposal/
├── materials/
├── planning/
├── sections/
├── reviews/
└── revisions/
```

If the user has no project skeleton, create one:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing init my-proposal --type nsfc --mode auto
```

Then run:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing next my-proposal --format json
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing taskpack my-proposal --format json
```

Follow the returned action and taskpack. Treat `taskpack.reference_inputs` as quality rules from the installed runtime's `scholar-writing/references/` directory.

## Agent Usage

Use installed custom agents when available:

- `scholar-architect`
- `scholar-writer`
- `scholar-reviewer`
- `scholar-revision`

Keep write boundaries from the taskpack. Critical issues, core-claim changes, large-scope restructuring, key fact changes, or broad cross-section impact require user confirmation.
EOF

cat > "$install_dir/bin/scholar-writing" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="$(cd "$script_dir/../runtime" && pwd)"
export SCHOLAR_WRITING_RUNTIME="$runtime_dir"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$runtime_dir/.uv-cache}"
exec uv run --project "$runtime_dir" scholar-writing "$@"
EOF
chmod +x "$install_dir/bin/scholar-writing"

cp "$stage_source/.codex/agents/"*.toml "$agents_dir/"

cat > "$install_dir/install-manifest.txt" <<EOF
skill_dir=$install_dir
runtime_dir=$runtime_dir
agents_dir=$agents_dir
installed_agents=scholar-architect.toml scholar-writer.toml scholar-reviewer.toml scholar-revision.toml
EOF

if [ "$sync_runtime" -eq 1 ]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required to pre-sync the runtime. Install uv or rerun with --no-sync." >&2
    exit 1
  fi
  uv sync --project "$runtime_dir"
fi

echo "ScholarWriting installed for Codex."
echo "Skill: $install_dir"
echo "Agents: $agents_dir"
echo "Restart Codex to refresh installed skills and agents."
