import argparse
import json
from pathlib import Path
import sys

import yaml

from .core.config import load_project_config
from .core.paths import find_repo_root
from .core.project import init_project
from .core.state import create_initial_state, read_state, state_path
from .core.taskpack import build_taskpack
from .core.workflow import advance_state, next_action as compute_next_action


def emit(data, output_format):
    """Print data in the requested output format."""
    if output_format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def load_state_or_initial(project_dir):
    """Read scores.yaml when present, otherwise return an initial state."""
    if state_path(project_dir).exists():
        return read_state(project_dir)
    return create_initial_state()


def command_status(args):
    state = load_state_or_initial(args.project_dir)
    emit(state, args.format)
    return 0


def command_next(args):
    repo_root = find_repo_root(Path(__file__))
    project_dir = Path(args.project_dir)
    config = load_project_config(project_dir, repo_root)
    state = load_state_or_initial(project_dir)
    emit(compute_next_action(project_dir, config, state), args.format)
    return 0


def command_init(args):
    repo_root = find_repo_root(Path(__file__))
    result = init_project(args.project_dir, repo_root, project_type=args.type, mode=args.mode, name=args.name)
    emit(result, args.format)
    return 0


def command_validate(args):
    repo_root = find_repo_root(Path(__file__))
    scripts_dir = repo_root / "scholar-writing" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    import validate as legacy_validate

    results = legacy_validate.validate_all(args.project_dir)
    data = {
        "valid": all(r.valid for r in results),
        "results": [r.to_dict() for r in results],
    }
    emit(data, args.format)
    return 0 if data["valid"] else 1


def command_taskpack(args):
    repo_root = find_repo_root(Path(__file__))
    project_dir = Path(args.project_dir)
    config = load_project_config(project_dir, repo_root)
    state = load_state_or_initial(project_dir)
    emit(build_taskpack(project_dir, config, state), args.format)
    return 0


def command_advance(args):
    repo_root = find_repo_root(Path(__file__))
    project_dir = Path(args.project_dir)
    config = load_project_config(project_dir, repo_root)
    state = load_state_or_initial(project_dir)
    if args.event_file:
        event = yaml.safe_load(Path(args.event_file).read_text(encoding="utf-8")) or {}
        state = advance_state(state, config, event=event)
        action = state.get("next_action", compute_next_action(project_dir, config, state))
    else:
        action = compute_next_action(project_dir, config, state)
        state["last_action"] = "advance_state"
        state["next_action"] = action
    if action["action"] == "ask_user":
        state["phase"] = "blocked"
        state["blocked_reason"] = action.get("reason")
    from .core.state import write_state
    write_state(project_dir, state)
    emit({"project_dir": str(project_dir), "next_action": action}, args.format)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="ScholarWriting deterministic workflow CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a standard ScholarWriting project skeleton")
    init.add_argument("project_dir", help="Project directory")
    init.add_argument("--type", choices=["nsfc", "paper"], default="nsfc")
    init.add_argument("--mode", choices=["auto", "from_materials", "from_outline", "from_draft"], default="auto")
    init.add_argument("--name", default=None)
    init.add_argument("--format", choices=["json", "yaml"], default="yaml")
    init.set_defaults(func=command_init)

    validate = subparsers.add_parser("validate", help="Validate a ScholarWriting project")
    validate.add_argument("project_dir", help="Project directory")
    validate.add_argument("--format", choices=["json", "yaml"], default="yaml")
    validate.set_defaults(func=command_validate)

    status = subparsers.add_parser("status", help="Read and print project scores.yaml")
    status.add_argument("project_dir", help="Project directory")
    status.add_argument("--format", choices=["json", "yaml"], default="yaml")
    status.set_defaults(func=command_status)

    next_cmd = subparsers.add_parser("next", help="Compute the next workflow action")
    next_cmd.add_argument("project_dir", help="Project directory")
    next_cmd.add_argument("--format", choices=["json", "yaml"], default="yaml")
    next_cmd.set_defaults(func=command_next)

    taskpack = subparsers.add_parser("taskpack", help="Build the current agent task pack")
    taskpack.add_argument("project_dir", help="Project directory")
    taskpack.add_argument("--format", choices=["json", "yaml"], default="yaml")
    taskpack.set_defaults(func=command_taskpack)

    advance = subparsers.add_parser("advance", help="Record the current next action into scores.yaml")
    advance.add_argument("project_dir", help="Project directory")
    advance.add_argument("--event-file", default=None, help="YAML event file, e.g. a review_result payload")
    advance.add_argument("--format", choices=["json", "yaml"], default="yaml")
    advance.set_defaults(func=command_advance)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
