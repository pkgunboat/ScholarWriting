---
name: scholar-writing
description: Use for academic writing workflows in this repository, including NSFC proposals, papers, proposal drafting, draft review, multi-agent writing, and write-review-revision optimization loops.
---

# ScholarWriting Codex Workflow

Use this skill when the user asks for academic writing, NSFC/国自然 proposal work, paper drafting, proposal review, draft optimization, or an automated write-review-revision loop.

## Ground Rules

- Treat `uv run scholar-writing next <project_dir> --format json` as the deterministic source of the next workflow action.
- Use `uv run scholar-writing taskpack <project_dir> --format json` to build the current agent handoff payload before delegating to a custom agent.
- Use `uv run scholar-writing advance <project_dir> --format json` to record the computed next action back into `scores.yaml`.
- Treat `scores.yaml` as the state source. Do not infer loop state only from prose.
- Use repo paths relative to the user's project directory, not relative to this skill directory.
- Do not use Claude Code `Agent(...)` pseudo-calls. In Codex, use project custom agents from `.codex/agents/` when agent delegation is appropriate.
- Use subagents only when the task boundary is clear and parallelism materially helps. Keep serial or tightly coupled state transitions in the main agent.
- Ordinary major/minor revision issues may be handled automatically. Critical, core-claim-changing, large-scope, or cross-section changes require user confirmation before editing sections.

## Required Loop

1. Identify the project directory. If the user does not provide one, use the current repository or ask for the intended project directory.
2. Run:

   ```bash
   uv run scholar-writing next <project_dir> --format json
   uv run scholar-writing taskpack <project_dir> --format json
   ```

3. Follow the returned `action`:

   - `run_architect`: use `scholar-architect` to produce or update `planning/outline.md`, `planning/claim_registry.md`, and `planning/dependency_graph.yaml`.
   - `run_writer`: use `scholar-writer` for the target chapter in `sections/`.
   - `run_reviewers`: use `scholar-reviewer`; run independent review dimensions in parallel only when the user asked for multi-agent review or the task clearly benefits.
   - `run_revision`: use `scholar-revision` only within the task pack write boundary.
   - `ask_user`: stop and ask the user for the missing input or required confirmation.

4. After every agent output, update or verify `scores.yaml`, then run `uv run scholar-writing next <project_dir> --format json` again.
5. Before claiming the workflow is complete, run:

   ```bash
   uv run pytest -q
   uv run scholar-writing validate <project_dir> --format json
   ```

## Expected Project Inputs

- `from_materials`: `materials/manifest.yaml` exists. Start with architect planning.
- `from_outline`: `planning/outline.md` exists. Start with chapter writing.
- `from_draft`: `sections/*.md` exists. Start with review and revision.

When `config.yaml` uses `input_mode: auto`, the CLI detects the effective mode in this priority: draft sections, outline, materials.
