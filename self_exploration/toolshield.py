#!/usr/bin/env python3
"""
ToolShield wrapper: generate test cases and distill experiences in sequence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import re
import requests

try:
    from self_exploration import tree_generation
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from self_exploration import tree_generation


DEFAULT_AGENT_CONFIG = Path("/mnt/data/MT-AgentRisk_ToolShield/evaluation/agent_config/config.toml")
DEFAULT_EVAL_DIR = Path("/mnt/data/MT-AgentRisk_ToolShield/evaluation")


class MCPInspector:
    """Minimal MCP inspector to list tool names via SSE JSON-RPC."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.sse_url = f"{self.base_url}/sse"
        self.message_url = f"{self.base_url}/message"
        self.session_url = None
        self._id = 0
        self._responses: Dict[int, Dict] = {}
        self._sse_thread = None
        self._connected = threading.Event()

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _listen_sse(self) -> None:
        try:
            resp = requests.get(self.sse_url, stream=True, timeout=(10, None))
            event_type = None
            for line in resp.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                line = line.strip()
                if line.startswith("event:"):
                    event_type = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    if event_type == "endpoint":
                        if data.startswith("http"):
                            self.session_url = data
                        else:
                            self.session_url = f"{self.base_url}{data}"
                        self._connected.set()
                    elif event_type == "message":
                        try:
                            msg = json.loads(data)
                            if "id" in msg:
                                self._responses[msg["id"]] = msg
                        except Exception:
                            pass
                    event_type = None
        except Exception as exc:
            print(f"[SSE] error: {exc}", file=sys.stderr)

    def _send(self, method: str, params: Optional[dict] = None) -> dict:
        rid = self._next_id()
        payload = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            payload["params"] = params

        url = self.session_url or self.message_url
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()

        for _ in range(100):
            if rid in self._responses:
                return self._responses.pop(rid)
            time.sleep(0.1)
        return {"error": "timeout waiting for response"}

    def connect(self) -> None:
        self._sse_thread = threading.Thread(target=self._listen_sse, daemon=True)
        self._sse_thread.start()
        if not self._connected.wait(timeout=10):
            raise RuntimeError("Timed out waiting for SSE endpoint event")

    def initialize(self) -> dict:
        return self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "toolshield-inspector", "version": "0.1.0"},
        })

    def list_tools(self) -> dict:
        return self._send("tools/list", {})


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


def _inspect_mcp_tools(base_url: str) -> Tuple[str, List[str]]:
    inspector = MCPInspector(base_url)
    inspector.connect()
    init_resp = inspector.initialize()
    tools_resp = inspector.list_tools()

    description = ""
    try:
        server_info = init_resp.get("result", {}).get("serverInfo", {})
        description = server_info.get("description") or server_info.get("name") or ""
    except Exception:
        description = ""

    tools = tools_resp.get("result", {}).get("tools", [])
    tool_names = [t.get("name") for t in tools if t.get("name")]
    if not tool_names:
        raise RuntimeError("No tools found from MCP server.")
    return description, tool_names


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
        lines.append(f"**• exp.{idx}: {rule}**")
    return "\n".join(lines) + "\n"


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
        "TOOLSHIELD_REPO_ROOT": "/mnt/data/MT-AgentRisk_ToolShield",
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

    runner = Path("/mnt/data/MT-AgentRisk_ToolShield/self_exploration/iterative_exp_runner.py")
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

    tool_description, tool_actions = _inspect_mcp_tools(args.mcp_server)

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


def main() -> None:
    parser = argparse.ArgumentParser(description="ToolShield wrapper CLI")
    parser.add_argument("--mcp_name", help="MCP tool name (e.g., PostgreSQL)")
    parser.add_argument("--mcp_server", help="MCP server base URL (e.g., http://localhost:8000)")
    parser.add_argument("--context_guideline", default=None, help="Optional context guideline")
    parser.add_argument("--output_path", help="Output directory for generated tasks")
    parser.add_argument("--exp_file", default=None, help="Experience JSON path (optional)")
    parser.add_argument("--agent", choices=["claude_code", "codex"], default=None, help="Target agent type")
    parser.add_argument("--source_location", default=None, help="Optional target file path")
    parser.add_argument("--agent-config", type=Path, default=DEFAULT_AGENT_CONFIG, help="Agent config TOML")
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR, help="Evaluation directory")
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
    gen.add_argument("--agent-config", type=Path, default=DEFAULT_AGENT_CONFIG, help="Agent config TOML")
    gen.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR, help="Evaluation directory")
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
