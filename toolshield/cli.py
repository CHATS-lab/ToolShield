#!/usr/bin/env python3
"""
ToolShield CLI — generate test cases and distill experiences in sequence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from toolshield import tree_generation
from toolshield._paths import default_agent_config, default_eval_dir, repo_root
from toolshield.inspector import inspect_mcp_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_env() -> Tuple[str, str]:
    model = os.getenv("TOOLSHIELD_MODEL_NAME")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not model or not api_key:
        raise RuntimeError(
            "Missing env vars. Set TOOLSHIELD_MODEL_NAME and OPENROUTER_API_KEY."
        )
    return model, api_key


def _update_config_toml(path: Path, model: str, api_key: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Agent config not found: {path}")
    if model and not model.startswith("openrouter/"):
        model = f"openrouter/{model}"
    lines = path.read_text().splitlines(keepends=True)

    def replace_in_section(section: str, key: str, value: str) -> None:
        start = None
        end = len(lines)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                name = stripped.strip("[]")
                if name == section:
                    start = i
                elif start is not None:
                    end = i
                    break
        if start is None:
            lines.extend([f"\n[{section}]\n", f'{key} = "{value}"\n'])
            return

        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if stripped.startswith(f"{key}"):
                lines[i] = f'{key} = "{value}"\n'
                return
        lines.insert(end, f'{key} = "{value}"\n')

    replace_in_section("llm.agent", "model", model)
    replace_in_section("llm.agent", "api_key", api_key)
    replace_in_section("llm.env", "model", model)
    replace_in_section("llm.env", "api_key", api_key)

    path.write_text("".join(lines))


def _find_agent_file(agent: str, source_location: Optional[str] = None) -> Path:
    if source_location:
        return Path(source_location).expanduser()

    home = Path.home()
    if agent == "claude_code":
        preferred = home / ".claude" / "CLAUDE.md"
    else:
        preferred = home / ".codex" / "AGENTS.md"

    preferred.parent.mkdir(parents=True, exist_ok=True)
    if not preferred.exists():
        preferred.write_text("")
    return preferred


def _load_experiences(exp_path: Path) -> Dict[str, str]:
    if not exp_path.exists():
        raise FileNotFoundError(f"Experience file not found: {exp_path}")
    with open(exp_path, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Experience file must be a JSON object")
    return data


def _get_max_exp_index(text: str) -> int:
    matches = re.findall(r"exp\.(\d+)", text)
    if not matches:
        return 0
    nums = [int(m) for m in matches if m.isdigit()]
    return max(nums) if nums else 0


def _format_experience_block(experiences: Dict[str, str], start_index: int) -> str:
    lines = []
    idx = start_index
    for _, rule in sorted(experiences.items(), key=lambda kv: kv[0]):
        idx += 1
        lines.append(f"**\u2022 exp.{idx}: {rule}**")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def import_experiences(args: argparse.Namespace) -> None:
    exp_path = Path(args.exp_file).expanduser()
    experiences = _load_experiences(exp_path)
    if not experiences:
        print("No experiences found in the JSON file. Nothing to import.")
        return

    target = _find_agent_file(args.agent, args.source_location)
    content = target.read_text() if target.exists() else ""

    header = "## Guidelines from Previous Experience"
    intro = (
        "The following guidelines have been identified from analyzing similar tasks. "
        "Please carefully consider these rules before taking any actions:\n\n"
    )
    tool_name = exp_path.stem.split("_")[-1]
    tool_line = f"Guidelines for the {tool_name}: \n\n"

    max_idx = _get_max_exp_index(content)
    block = _format_experience_block(experiences, max_idx)

    if header in content:
        append_text = "\n" + tool_line + block
    else:
        append_text = "\n" + header + "\n\n" + intro + tool_line + block

    target.write_text(content + append_text)
    print(f"Injected {len(experiences)} guidelines into: {target}")


def _run_iterative_runner(
    task_root: Path,
    output_dir: Path,
    exp_file: Path,
    mcp_name: str,
    agent_config: Path,
    eval_dir: Path,
    server_hostname: str,
    debug: bool = False,
) -> None:
    env = os.environ.copy()
    env.update({
        "TOOLSHIELD_REPO_ROOT": str(repo_root()),
        "TOOLSHIELD_TASK_ROOT": str(task_root),
        "TOOLSHIELD_TASK_BASE_DIR": str(task_root),
        "TOOLSHIELD_OUTPUT_DIR": str(output_dir),
        "TOOLSHIELD_STATE_BASE_DIR": str(output_dir),
        "TOOLSHIELD_EXPERIENCE_FILE": str(exp_file),
        "TOOLSHIELD_TREE_PATH": str(task_root / f"{mcp_name.lower()}_safety_tree.json"),
        "TOOLSHIELD_EVAL_DIR": str(eval_dir),
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    exp_file.parent.mkdir(parents=True, exist_ok=True)

    runner = Path(__file__).resolve().parent / "iterative_exp_runner.py"
    cmd = [
        sys.executable,
        str(runner),
        "--task-root", str(task_root),
        "--output-dir", str(output_dir),
        "--experience-file", str(exp_file),
        "--eval-dir", str(eval_dir),
        "--agent-llm-config", "agent",
        "--agent-llm-config-file", str(agent_config),
        "--env-llm-config", "env",
        "--env-llm-config-file", str(agent_config),
        "--server-hostname", server_hostname,
    ]
    if debug:
        cmd.append("--debug")
    result = subprocess.run(cmd, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"iterative_exp_runner failed with exit code {result.returncode}")


def generate(args: argparse.Namespace) -> None:
    if getattr(args, "multi_turn", False):
        print("Note: --multi-turn is always enabled; flag is ignored.")
    model, api_key = _require_env()
    _update_config_toml(args.agent_config, model, api_key)

    tool_description, tool_actions = inspect_mcp_tools(args.mcp_server)

    output_dir = Path(args.output_path)
    tree_generation.run_generation(
        mcp_name=args.mcp_name,
        tools_list=tool_actions,
        tool_description=tool_description,
        context_guideline=args.context_guideline,
        output_dir=output_dir,
        enable_multi_turn=True,
        skip_benign=True,
        debug=args.debug,
    )

    if args.exp_file:
        exp_file = Path(args.exp_file)
    else:
        model_short = model.split("/")[-1] if model else "model"
        tool_name = args.mcp_name.lower()
        exp_file = output_dir.parent / f"experience_list_{model_short}_{tool_name}.json"
    state_output = output_dir.parent / "exp_output"
    _run_iterative_runner(
        task_root=output_dir,
        output_dir=state_output,
        exp_file=exp_file,
        mcp_name=args.mcp_name,
        agent_config=args.agent_config,
        eval_dir=args.eval_dir,
        server_hostname=args.server_hostname,
        debug=args.debug,
    )
    if not args.debug:
        print(f"Done. Experience file updated at: {exp_file}")


def _build_import_args_from_generate(args: argparse.Namespace, exp_file: Path) -> argparse.Namespace:
    return argparse.Namespace(
        exp_file=str(exp_file),
        agent=args.agent,
        source_location=args.source_location,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="toolshield",
        description="ToolShield \u2014 training-free defense for tool-using AI agents",
    )
    parser.add_argument("--mcp_name", help="MCP tool name (e.g., PostgreSQL)")
    parser.add_argument("--mcp_server", help="MCP server base URL (e.g., http://localhost:8000)")
    parser.add_argument("--context_guideline", default=None, help="Optional context guideline")
    parser.add_argument("--output_path", help="Output directory for generated tasks")
    parser.add_argument("--exp_file", default=None, help="Experience JSON path (optional)")
    parser.add_argument("--agent", choices=["claude_code", "codex"], default=None, help="Target agent type")
    parser.add_argument("--source_location", default=None, help="Optional target file path")
    parser.add_argument("--agent-config", type=Path, default=default_agent_config(), help="Agent config TOML")
    parser.add_argument("--eval-dir", type=Path, default=default_eval_dir(), help="Evaluation directory")
    parser.add_argument("--server-hostname", default=os.environ.get("SERVER_HOST", "localhost"), help="Runtime server hostname")
    parser.add_argument("--debug", action="store_true", help="Show verbose logs and underlying runner output")
    sub = parser.add_subparsers(dest="command", required=False)

    gen = sub.add_parser("generate", help="Generate test cases and distill experiences")
    gen.add_argument("--mcp_name", required=True, help="MCP tool name (e.g., PostgreSQL)")
    gen.add_argument("--mcp_server", required=True, help="MCP server base URL (e.g., http://localhost:8000)")
    gen.add_argument("--context_guideline", default=None, help="Optional context guideline")
    gen.add_argument("--output_path", required=True, help="Output directory for generated tasks")
    gen.add_argument("--exp_file", default=None, help="Experience JSON path (optional)")
    gen.add_argument("--multi-turn", action="store_true", help=argparse.SUPPRESS)
    gen.add_argument("--agent-config", type=Path, default=default_agent_config(), help="Agent config TOML")
    gen.add_argument("--eval-dir", type=Path, default=default_eval_dir(), help="Evaluation directory")
    gen.add_argument("--server-hostname", default=os.environ.get("SERVER_HOST", "localhost"), help="Runtime server hostname")
    gen.add_argument("--debug", action="store_true", help="Show verbose logs and underlying runner output")
    gen.add_argument("--agent", choices=["claude_code", "codex"], default=None, help="Target agent type")
    gen.add_argument("--source_location", default=None, help="Optional target file path")
    gen.set_defaults(func=generate)

    imp = sub.add_parser("import", help="Inject experience guidelines into agent instructions")
    imp.add_argument("--exp-file", required=True, help="Experience JSON to inject")
    imp.add_argument(
        "--agent",
        choices=["claude_code", "codex"],
        default="claude_code",
        help="Target agent type",
    )
    imp.add_argument("--source_location", default=None, help="Optional target file path")
    imp.set_defaults(func=import_experiences)

    args = parser.parse_args()
    if args.command is None:
        missing = [name for name in ["mcp_name", "mcp_server", "output_path", "agent"] if not getattr(args, name)]
        if missing:
            parser.error(f"Missing required arguments for end-to-end mode: {', '.join('--' + m for m in missing)}")
        generate(args)
        exp_file = Path(args.exp_file) if args.exp_file else None
        if exp_file is None:
            model, _ = _require_env()
            model_short = model.split("/")[-1] if model else "model"
            tool_name = args.mcp_name.lower()
            exp_file = Path(args.output_path).parent / f"experience_list_{model_short}_{tool_name}.json"
        import_experiences(_build_import_args_from_generate(args, exp_file))
        return

    args.func(args)


if __name__ == "__main__":
    main()
