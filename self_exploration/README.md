# ToolShield (Self Exploration)

This folder contains the ToolShield self-exploration pipeline. It generates safety test cases from a live MCP server, runs them, and distills safety experiences.

**What it does**
1. Inspect MCP server to fetch tool/function names.
2. Generate a safety tree and test cases (single-turn + multi-turn).
3. Execute tasks and distill experiences into an experience JSON.

## Requirements
- A running MCP server (with SSE endpoint).
- `TOOLSHIELD_MODEL_NAME` and `OPENROUTER_API_KEY` in the environment.
- Python environment with dependencies for `self_exploration` and `evaluation`.

## Quick Start

1. Set env vars:

```bash
export TOOLSHIELD_MODEL_NAME="bytedance-seed/seed-1.6"
export OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
```

2. Run ToolShield (end-to-end: generate + import):

This runs the full pipeline: **inspect MCP → generate safety tree → generate tests → distill experiences → inject into agent context memory**.

```bash
python self_exploration/toolshield.py \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path /mnt/data/MT-AgentRisk_ToolShield/self_exploration/exp_examples \
  --agent codex \
```

- `--agent`: now only support `claude_code` or `codex`.
- `--context_guideline` (optional): replaces the default context guidance in prompts.
- `--exp_file` (optional): path to an existing experience JSON that will be updated in-place.
- `--source_location` (optional): customized file path to inject the guidelines into.

At the end, the experience file is updated at:
`<output_path>/../experience_list_{model_name}_{tool}.json` (or your `--exp_file`).

## Other Commands

Generate only:

```bash
python self_exploration/toolshield.py generate \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path /mnt/data/MT-AgentRisk_ToolShield/self_exploration/exp_examples \
  --context_guideline "Context information for the current tool (optional)" \
  --exp_file /path/to/existing_experience.json
```

Import only:

```bash
python self_exploration/toolshield.py import \
  --exp-file /path/to/experience_list.json \
  --agent codex \
  --source_location /path/to/AGENTS.md
```

## Outputs
- Safety tree: `<output_path>/<mcp_name_lower>_safety_tree.json`
- Test cases: `<output_path>/task.*` and `<output_path>/multi_turn_task.*`
- Generation summary: `<output_path>/generation_summary.json`
- Experience list: by default `<output_path>/../experience_list.json`
- Run outputs (state/summaries): `<output_path>/../exp_output`

## Notes

1. ToolShield currently supports **OpenRouter only**. When exporting `TOOLSHIELD_MODEL_NAME`, **do not** include the `openrouter/` prefix. Example: `bytedance-seed/seed-1.6` (ToolShield adds the prefix when writing the config).
2. Currently supported MCP tools: `filesystem`, `terminal`, `postgres`, `playwright`, `notion`.

## Common Issues

**1) Missing env vars**
```
Missing env vars. Set TOOLSHIELD_MODEL_NAME and OPENROUTER_API_KEY.
```
Fix: export both variables before running.

**2) MCP connection timeout**
```
[SSE] error: ... Read timed out.
```
Fix: verify the MCP server and its SSE endpoint:
```bash
curl -v http://localhost:9091/sse
```
