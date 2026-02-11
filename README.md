

<div align="center">
<h1>ToolShield: Training-Free Defense for Multi-Turn Safety Risks in Tool-Using AI Agents</h1>

[![PyPI](https://img.shields.io/pypi/v/toolshield?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/toolshield/) [![Python](https://img.shields.io/pypi/pyversions/toolshield?style=for-the-badge&logo=python&logoColor=white&label=)](https://pypi.org/project/toolshield/) [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE) [![Homepage](https://img.shields.io/badge/Homepage-4d8cd8?style=for-the-badge&logo=google-chrome&logoColor=white)](https://unsafer-in-many-turns.github.io) [![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-FFD21E?style=for-the-badge)](https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk)

<strong>Supports:</strong>&nbsp;
<a href="#use-pre-generated-experiences"><img src="https://img.shields.io/badge/Claude_Code-D97757?style=flat-square&logo=anthropic&logoColor=white" alt="Claude Code"></a>
<a href="#use-pre-generated-experiences"><img src="https://img.shields.io/badge/Codex-000000?style=flat-square&logo=data:image/png;base64,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&logoColor=white" alt="Codex"></a>
<a href="#use-pre-generated-experiences"><img src="https://img.shields.io/badge/Cursor-00A3E0?style=flat-square&logo=cursor&logoColor=white" alt="Cursor"></a>
<a href="#use-pre-generated-experiences"><img src="https://img.shields.io/badge/OpenHands-E5725E?style=flat-square&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAChUlEQVR42u2bQWsTQRTHf2+yuyU2aBIQFHKRXupVerLfXb+AtyJ40IMUwYOFgFSb3ck8D0lEsN2Z7GazpHkv5DSbx8xvZ+a9/OeNzOdz5YjNceR29ACytg4UTXoKBEG28Ln6TcxSfXYGIJcTBKnBoOv2gNcqsVM5TgZrEFIzePBaJr6EHQMQBK8lV4t3eMoHOyoISzwjmXBevK3trKJkUvC5/MDN8ppMisjglPPiklMZs8Q3mg0tZoAQCHzzn1joL+SB7UQQPCVTN+N1cRl9W4LjJlzztbqikCFKqAV2ll8gIv0uAUVrATgG5FJs0amCQoZJAHrfAxSt7STr9b/NOt343HzbbcAWBg2AATAABsAAGAADYAAMgAEwAAbAABiAXesB8s+nSXvMKy0Fj84BeCo8ZVQS81TJPgMer+VaGK0XRNqKIlnbtz92L/C6oF4UrXjqnif5VJSRTJgOZmu5LdQ+nZG3giBtj8YElzRJV0p/2GoBpM2W0O8SWOl2u7VdTG2LAgbAABgAA2AA9hIG+62wOYD6gC4HfwD1Ad3aAdQHdDv8A6gP6BrAAdQHdAvAwqABMAAGwAAYgN7D4Ka2tz5tTc8WUyuQ24fBVqKootyGeVS6zuWE7/4LHxfvydaJ0/2QHJX+5qy44FX+hkrvoonOqRszIGsMo7Us/iwidyuBQp7wU34kdVJRhjJi4l5S6m00wwws+/kztLHYgYcScJQEfLLPQPh7mBID0HsqHO9AsyOuZkdqFgUMgAEwAHveBJtsbPF2eXwAVpemSkRcbSLktSSwfFwAFKWQIdPBrPYilOCo5I6hjPamMsm+rs7KlvcG93XesMcloL0folgUMAAG4D/7A9TtGBfNiHvGAAAAAElFTkSuQmCC&logoColor=white" alt="OpenHands"></a>
<a href="#use-pre-generated-experiences"><img src="https://img.shields.io/badge/OpenClaw-FF6B6B?style=flat-square&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAADi0lEQVR42u2az24bVRTGv+/cuWPHaWqRKopEgGbJigVCqrqjj8BbIPE2vAM7nqAv0EWlrpBAYgFd0FKkoqTFSWfm3ntYjO2GZu54UlsNSc6V7IV9fez7m/PnO2fMo6MjxQ1eghu+bjyAovNVVeC6BQYBkMMAsHSgkxbEdTm9KlIdVwBQBUuH40d/4PT3I8iouAYQCA0J/s4Yu18fQt85zzsAAArx5ukxXj/5E7LtgXjFAQihVcTos9vYfXB4LrSzISATD9nyQLriAEiok9abL5QE05nHVU9+SbOhbDrAABgAA2AArBdYZ+nyaXU94qZtduv7DwdAFXvffI5ybwINEZ0nVIWMC8x+eYmXD3+DjF1WW1CIeBowvX+A6b2PkU5D9oAUIr0JePHjz4inAXR8rwZubQ8o9yYYHdyC1rH7xyaFTDzqFyfD+oqkKHZKjA52EGcNKOz0EDoizppL9gAA2iRoHaF16nbxBGgRoSENtxn1rU3JhIgjtEn/gxyw6LMz/Taob9/flE3g4jatChgAA2AABifBZRIakGjOzg7YXdbafnyAzcX7ALRvFqFn+nz+93NZm7wAAA0JWgVoIT0DkfZQMiogEw91AnTV7KiQLQ96QarmgiVnU9juEcKNPZDaet9VWlkQqgptElIVIIV0CyESWodsySy6rqjfnWB8dwqOi7xqY1uvT379G/VfM2hMWSXI0qF69hpbh1Ow7FGCJHwTEY4rvHryHNpk1OVCCVYBfm8Cf2er3ZYBgCbB70+67XTeGhO2HtVz8Vm0Suzp948R/6nBvitQBYwPp/j02y+hfUPWuWp8/sNPePX4GWS7XOmBn3z3FcYHt6BV7AmD+fYOW0Xuh+iqZiW2BmVUQJPmtTgJdQS9QIOeG0uf+96QwILzoWzRP5Oc5wmN2h6Om0qCF2yIlslIM/SXSXBAk7fYM2Qou4F7FqYDDIABMAAmhdcaBwiXj6wQEXarROQl8dLmqnJ8qQAUiCdNO7rq0wF1bOd7A4chqQoIsxpuUQ5XleAPDoCAqoJe8NGDu63OZs/mmOBuj/pF0AJWk7DzxT7K/W3Qu/5ar4DbKVt1+Z6zQa71LzG2zdAgBZYUqYqDvEpGDnQc5OGpimt5wUZCYCCrYXlgHgJDRR6Fl58EN77IdafdVgYNgAEwAAbAABgAA2AADIABMAAGwAAYAANgAAyAATAABsAAGIDz618kzZpJrX5jHAAAAABJRU5ErkJggg==&logoColor=white" alt="OpenClaw"></a>

</div>

---

<p align="center">
  <a href="#quickstart">Quickstart</a> |
  <a href="#use-pre-generated-experiences">Pre-generated</a> |
  <a href="#generate-your-own">Generate Your Own</a> |
  <a href="#extend-to-new-tools">Extend</a> |
  <a href="#mt-agentrisk-benchmark">Benchmark</a> |
  <a href="#citation">Citation</a>
</p>

**ToolShield** is a training-free, tool-agnostic defense for AI agents that use MCP tools. It works by letting the agent explore tool functionality in a sandbox, learning from its own executions, and distilling safety guidelines before deployment. Reduces attack success rate by **30%** on average — with zero fine-tuning.

<p align="center">
  <img src="overview.jpg" alt="Overview" width="75%">
</p>

## Quickstart

```bash
pip install toolshield
```

### Use Pre-generated Experiences

We ship safety experiences for 6 models across 5 tools, with plug-and-play support for **5 coding agents**. Inject them in one command:

```bash
# For Claude Code
toolshield import \
  --exp-file experiences/claude-sonnet-4.5/experience_list_claude-sonnet-4.5_postgres.json \
  --agent claude_code

# For Codex
toolshield import \
  --exp-file experiences/claude-sonnet-4.5/experience_list_claude-sonnet-4.5_postgres.json \
  --agent codex

# For OpenClaw
toolshield import \
  --exp-file experiences/claude-sonnet-4.5/experience_list_claude-sonnet-4.5_postgres.json \
  --agent openclaw

# For Cursor (writes to global user rules via SQLite)
toolshield import \
  --exp-file experiences/claude-sonnet-4.5/experience_list_claude-sonnet-4.5_postgres.json \
  --agent cursor

# For OpenHands (creates a microagent)
toolshield import \
  --exp-file experiences/claude-sonnet-4.5/experience_list_claude-sonnet-4.5_postgres.json \
  --agent openhands
```

This appends safety guidelines to your agent's context file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.openclaw/workspace/AGENTS.md`, Cursor's global user rules, or `~/.openhands/microagents/toolshield.md`). To remove them:

```bash
toolshield unload --agent claude_code
```

Available experiences in `experiences/`:

| Model | 📁 Filesystem | 🐘 PostgreSQL | 💻 Terminal | 🎭 Playwright | 📝 Notion |
|-------|:---:|:---:|:---:|:---:|:---:|
| `claude-sonnet-4.5` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `gpt-5.2` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `deepseek-v3.2` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `gemini-3-flash-preview` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `qwen3-coder-plus` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `seed-1.6` | ✅ | ✅ | ✅ | ✅ | ✅ |

> More plug-and-play experiences for additional tools coming soon (including [Toolathlon](https://github.com/toolathlon) support)! Have a tool you'd like covered? [Open an issue](https://github.com/CHATS-Lab/ToolShield/issues).

### Generate Your Own

Point ToolShield at any running MCP server to generate custom safety experiences:

```bash
export TOOLSHIELD_MODEL_NAME="anthropic/claude-sonnet-4.5"
export OPENROUTER_API_KEY="your-key"

# Full pipeline: inspect → generate safety tree → test → distill → inject
toolshield \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path output/postgres \
  --agent codex
```

Or generate without injecting (useful for review):

```bash
toolshield generate \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path output/postgres
```

### Extend to New Tools

ToolShield works with any MCP server that has an SSE endpoint:

```bash
toolshield generate \
  --mcp_name your_custom_tool \
  --mcp_server http://localhost:PORT \
  --output_path output/your_custom_tool
```

## MT-AgentRisk Benchmark

We also release **MT-AgentRisk**, a benchmark of 365 harmful tasks across 5 MCP tools, transformed into multi-turn attack sequences. See [`agentrisk/README.md`](agentrisk/README.md) for full evaluation setup.

**Quick evaluation:**

```bash
# 1. Download benchmark tasks
git clone https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk
cp -r MT-AgentRisk/workspaces/* workspaces/

# 2. Run a single task (requires OpenHands setup — see agentrisk/README.md)
python agentrisk/run_eval.py \
  --task-path workspaces/terminal/multi_turn_tasks/multi-turn_root-remove \
  --agent-llm-config agent \
  --env-llm-config env \
  --outputs-path output/eval \
  --server-hostname localhost
```

Add `--use-experience <path>` to evaluate with ToolShield defense.

## Repository Layout

```
ToolShield/
├── toolshield/          # pip-installable defense package
├── agentrisk/           # evaluation framework (see agentrisk/README.md)
├── experiences/         # pre-generated safety experiences (6 models × 5 tools)
├── workspaces/          # MT-AgentRisk task data (from HuggingFace)
├── docker/              # Dockerfiles and compose
└── scripts/             # experiment reproduction guides
```

## Acknowledgments

We thank the authors of the following projects for their contributions:

- [OpenAgentSafety](https://github.com/sani903/OpenAgentSafety)
- [SafeArena](https://github.com/McGill-NLP/safearena)
- [MCPMark](https://github.com/eval-sys/mcpmark)

## Citation

```bibtex
```

## License

MIT
