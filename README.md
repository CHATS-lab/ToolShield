

<div align="center">
<h1>ToolShield: Training-Free Defense for Multi-Turn Safety Risks in Tool-Using AI Agents</h1>

[![PyPI](https://img.shields.io/pypi/v/toolshield?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/toolshield/) [![Python](https://img.shields.io/pypi/pyversions/toolshield?style=for-the-badge&logo=python&logoColor=white&label=)](https://pypi.org/project/toolshield/) [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE) [![Homepage](https://img.shields.io/badge/Homepage-4d8cd8?style=for-the-badge&logo=google-chrome&logoColor=white)](https://unsafer-in-many-turns.github.io) [![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-FFD21E?style=for-the-badge)](https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk)
</div>

---

<p align="center">
  <a href="#quickstart">Quickstart</a> |
  <a href="#installation">Install</a> |
  <a href="#mt-agentrisk-benchmark">Benchmark</a> |
  <a href="#reproducing-experiments">Reproduce Results</a> |
  <a href="#adding-new-tools">Extend</a> |
  <a href="#citation">Citation</a>
</p>

The safety-capability gap in LLM-based agents widens as they engage in multi-turn interactions and employ diverse tools, introducing risks overlooked by existing benchmarks. This repository contains:

1. **ToolShield** (`toolshield/`) — a pip-installable, training-free defense where agents explore tool functionality in a sandbox, learn from executions, and distill safety experiences before deployment. Reduces ASR by **30%** on average.

2. **MT-AgentRisk** (`workspaces/`) — a benchmark of 365 harmful tasks across five MCP tool categories (Filesystem, PostgreSQL, Terminal, Playwright/Browser, Notion), transformed into multi-turn attack sequences. ASR increases by **16%** on average compared to single-turn.

<p align="center">
  <img src="overview.jpg" alt="Overview" width="75%">
</p>

## Installation

```bash
pip install toolshield
```

**From source (development):**

```bash
git clone https://github.com/CHATS-Lab/ToolShield.git
cd ToolShield
pip install -e ".[dev]"
```

**Docker:**

```bash
docker build -f docker/Dockerfile -t toolshield:latest .
docker run toolshield --help
```

## Quickstart

ToolShield requires a running MCP server and two environment variables:

```bash
export TOOLSHIELD_MODEL_NAME="anthropic/claude-sonnet-4.5"
export OPENROUTER_API_KEY="your-key"
```

**End-to-end** — generate safety tree, test cases, distill experiences, and inject into agent context:

```bash
toolshield \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path output/postgres \
  --agent codex
```

**Generate only** — produce test cases and experiences without importing:

```bash
toolshield generate \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path output/postgres
```

**Import only** — inject pre-generated experiences into an agent's context:

```bash
toolshield import \
  --exp-file experiences/claude-sonnet-4.5/experience_list_claude-sonnet-4.5_postgres.json \
  --agent codex
```

## Reproducing Experiments

For complete experiment instructions with exact commands, parameter settings, and expected outputs, see **[scripts/EXPERIMENTS.md](scripts/EXPERIMENTS.md)**.

Or use Docker to spin up all MCP servers and the evaluation environment in one command:

```bash
docker compose -f docker/docker-compose.yml up -d
```

## MT-AgentRisk Benchmark

The benchmark dataset is hosted on [HuggingFace](https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk). Download tasks into `workspaces/`:

```bash
git clone https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk
cp -r MT-AgentRisk/workspaces/* workspaces/
```

Each task directory contains:

| File | Description |
|------|-------------|
| `task.md` / `task-turn-*.md` | Instructions shown to the agent |
| `workspace/` | Pre-seeded sandbox filesystem contents |
| `utils/dependencies.yml` | MCP tools required by the task |

Pre-generated safety experiences from six models are included in `experiences/`.

## Adding New Tools

1. Start your MCP server with an SSE endpoint
2. Run ToolShield against it:
   ```bash
   toolshield generate --mcp_name my_tool --mcp_server http://localhost:PORT --output_path output/my_tool
   ```
3. Add the tool to `MCP_REGISTRY` in `agentrisk/run_eval.py` for evaluation

## Repository Layout

```
ToolShield/
├── toolshield/          # pip-installable defense package
├── agentrisk/           # evaluation benchmark runner
├── experiences/         # pre-generated safety experiences
├── workspaces/          # MT-AgentRisk task data
├── docker/              # Dockerfiles and compose
├── scripts/             # reproduction guides
└── pyproject.toml
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
