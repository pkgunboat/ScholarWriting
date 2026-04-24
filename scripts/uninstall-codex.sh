#!/usr/bin/env bash
set -euo pipefail

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-sync)
      shift
      ;;
    --help|-h)
      cat <<'EOF'
Usage: scripts/uninstall-codex.sh

Remove ScholarWriting from the local Codex home.

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

codex_home="${CODEX_HOME:-$HOME/.codex}"
install_dir="${SCHOLAR_WRITING_INSTALL_DIR:-$codex_home/skills/scholar-writing}"
agents_dir="${SCHOLAR_WRITING_AGENTS_DIR:-$codex_home/agents}"

rm -rf "$install_dir"
rm -f \
  "$agents_dir/scholar-architect.toml" \
  "$agents_dir/scholar-writer.toml" \
  "$agents_dir/scholar-reviewer.toml" \
  "$agents_dir/scholar-revision.toml"

echo "ScholarWriting removed from Codex."
