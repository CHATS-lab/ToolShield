# Unsafer in Many Turns: Benchmarking and Defending Multi-Turn Safety Risks in Tool-Using Agents

This repository contains the code and data for **MT-AgentRisk**, a benchmark for evaluating multi-turn safety in tool-using agents, and **ToolShield**, a training-free defense that leverages the agent's own capabilities to improve safety awareness.

## Overview
![Overview](overview.jpg)

LLM-based agents can take actions that cause real-world harm, yet current safety mechanisms focus primarily on single-turn, text-based interactions. This work addresses this gap with:

1. **A principled attack taxonomy** that transforms single-turn harmful tasks into multi-turn attack sequences across three dimensions: Format, Method, and Target.

2. **MT-AgentRisk Benchmark**: 365 single-turn harmful tasks across five tools (Filesystem-MCP, Browser/Playwright-MCP, PostgreSQL-MCP, Notion-MCP, Terminal), transformed into multi-turn attack sequences using our taxonomy (Currently only contains 40 multi + 40 single, will upload the full dataset afterwards).

3. **ToolShield Defense**: A training-free, tool-agnostic defense where agents explore tool functionality in a sandbox, learn from their own executions, and distill safety experiences before deployment.


## Key Results

Our evaluations reveal significant safety degradation in multi-turn settings:
- **Attack**: ASR increases by 27% for Claude-4.5-Sonnet, 23% for Qwen3-Coder, and 14% for GPT-5.2 when harm is distributed across turns.
- **Defense**: ToolShield reduces ASR by 50% for Claude-4.5-Sonnet, 24% for Gemini-3-Flash, and 19% for GPT-5.2 in multi-turn settings.

## Repository Layout
```
./
├── workspaces/                              # Runnable task bundles (inputs to evaluation)
│   ├── single_turn_tasks/                   # Single-turn tasks 
│   │   └── <tool>/                          # Tool environment: fs/playwright/postgres/terminal/notion
│   │       └── <task_name>/
│   │           ├── task.md                  # Instruction shown to the agent
│   │           ├── workspace/               # Pre-seeded sandbox filesystem contents
│   │           └── utils/
│   │               ├── evaluator.py         # Programmatic scoring logic
│   │               └── dependencies.yml     # MCP/tools required by this task
│   ├── multi_turn_tasks (MT-AgentRisk)/     # Multi-turn tasks
│   │   └── <tool>/
│   │       └── <task_name>/
│   │           ├── turns.yml                # Turn manifest (order, patterns)
│   │           ├── task-turn-*.md           # Per-turn instructions
│   │           ├── workspace/               # Pre-seeded contents
│   │           └── utils/
│   │               ├── evaluator.py
│   │               └── dependencies.yml
├── evaluation/                              # Task execution and scoring harness
│   ├── run_eval.py                          # Main runner (loads task, sets up MCP, runs agent)
│   ├── post_eval.py                         # LLM-as-judge scoring
│   ├── run_together.sh                      # Batch execution script
│   ├── agent_config/                        # Agent LLM configurations
│   │   ├── config_model.toml
│   │   └── ...
│   └── README.md
├── task_decomposition (MTR)/                # Attack taxonomy: single-turn → multi-turn
│   ├── run_decomposition.py                 # CLI to generate multi-turn task bundles
│   ├── decomposition_prompt.py              # Prompt template for decomposition
└── self_exploration (ToolShield)/           # ToolShield: self-exploration defense pipeline
    ├── tree_generation.py                   # Generates safety trees + test case bundles
    ├── iterative_exp_runner.py              # Iterative experience generation
    ├── prompts.py                           # Prompt templates
    ├── post_process_prompts.py              # Shared utilities
    └── experience_list_*.json               # Generated safety experiences per model/tool
```

## Quick Start

### 1. Environment Preparation

#### 1.1 Clone and Patch OpenHands
```bash
# Clone OpenHands 0.54.0
git clone --branch 0.54.0 --single-branch https://github.com/All-Hands-AI/OpenHands.git
# Apply our schema overrides
cp MT-AgentRisk_ToolShield/evaluation/client.py OpenHands/openhands/mcp/client.py
```

#### 1.2 Clone MCPMark
```bash
git clone https://github.com/eval-sys/mcpmark.git MT-AgentRisk_ToolShield/mcpmark-main
```

> 📝 Follow [this guide](https://github.com/eval-sys/mcpmark/blob/main/docs/mcp/notion.md) to get your `NOTION_TOKEN`.

#### 1.3 Pull Docker Images
```bash
# TODO: Add our Docker Hub images
```

#### 1.4 Export Environment Variables
```bash
export TOOLSHIELD_MODEL_NAME="bytedance-seed/seed-1.6"
export OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
export NOTION_TOKEN="YOUR_NOTION_TOKEN"
```

> ⚠️ When setting `TOOLSHIELD_MODEL_NAME`, **do not** include the `openrouter/` prefix.

#### 1.5 Start MCP Servers

```bash

bash MT-AgentRisk_ToolShield/evaluation/start_mcp_servers.sh

```

This will start all required MCP services (Notion, Filesystem, etc.) in the background.

### 2. Running ToolShield Defense (Self-Exploration)

This runs the full ToolShield pipeline: **Inspect MCP → Generate Safety Tree → Generate Tests → Distill Experiences → Inject into Agent Context**.
```bash
python self_exploration/toolshield.py \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path /mnt/data/MT-AgentRisk_ToolShield/self_exploration/exp_examples \
  --agent codex
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `--agent` | Agent type: `claude_code` or `codex` |
| `--context_guideline` | (Optional) Custom context guidance to replace the default |
| `--exp_file` | (Optional) Path to existing experience JSON to update in-place |
| `--source_location` | (Optional) Custom file path for guideline injection |

#### Output

The experience file is saved to:
```
<output_path>/../experience_list_{model_name}_{tool}.json
```

For more details, see `MT-AgentRisk_ToolShield/self_exploration/README.md`.

---

### 3. Running Evaluation

Use `evaluation/run_eval.py` to evaluate agents on tasks.

#### Agent Configuration

Agent configurations are defined in TOML files under `evaluation/agent_config/`:
```toml
# Example: evaluation/agent_config/config_deepseek3.2exp.toml
[llm.agent]
model = "openrouter/deepseek/deepseek-v3.2-exp"
base_url = "https://openrouter.ai/api/v1"
api_key = ""
max_output_tokens = 16384

[llm.env]
model = "openrouter/deepseek/deepseek-v3.2-exp"
base_url = "https://openrouter.ai/api/v1"
api_key = ""
max_output_tokens = 16384
```

#### Run a Single Task
```bash
poetry run python evaluation/run_eval.py \
  --task-path workspaces/single_turn_tasks/single_playwright/safety-aid-misogyny \
  --agent-llm-config agent \
  --env-llm-config env \
  --outputs-path evaluation/test_output \
  --use-experience experience.json \
  --server-hostname localhost
```

#### Run Tasks Sequentially

Modify and run `evaluation/run_together.sh` to execute multiple tasks in sequence:
```bash
bash evaluation/run_together.sh
```

#### Post Evaluation (LLM-as-Judge)

After task execution, run the post-evaluation script:
```bash
python evaluation/post_eval.py \
  --tasks-dir <path-to-task-directory> \
  --output-dir <path-to-output-logs>
```

| Argument | Description |
|----------|-------------|
| `--tasks-dir` | Relative path to the task directory |
| `--output-dir` | Relative path containing `traj/eval/state` logs |

> ⚠️ Due to ethical concerns, we currently do not plan to release the full decomposition prompts. A template is available in Appendix E.8 of the paper.

---

### 4. Adding New Tools

To integrate new MCP tools, add the tool name and host address to `MCP_REGISTRY` in `evaluation/run_eval.py`:
```python
MCP_REGISTRY = {
    "mcp-filesystem": "http://localhost:9090/sse",
    "mcp-postgres":   "http://localhost:9091/sse",
    "mcp-playwright": "http://localhost:9092/sse",
    "mcp-notion":     "http://localhost:9097/sse",
}
```

> ⚠️ Don't forget to add your new tool to `dependencies.yml` in each task folder that requires it:
> `workspaces/<task_type>/<tool>/<task_name>/utils/dependencies.yml`

## References
```bibtex
@article{vijayvargiya2025openagentsafety,
  title={OpenAgentSafety: A Comprehensive Framework for Evaluating Real-World AI Agent Safety},
  author={Vijayvargiya, Sanidhya and Soni, Aditya Bharat and Zhou, Xuhui and Wang, Zora Zhiruo and Dziri, Nouha and Neubig, Graham and Sap, Maarten},
  journal={arXiv preprint arXiv:2507.06134},
  year={2025}
}

@inproceedings{tur2025safearena,
  title={SafeArena: Evaluating the Safety of Autonomous Web Agents},
  author={Tur, Ada Defne and Meade, Nicholas and L{\"u}, Xing Han and Zambrano, Alejandra and Patel, Arkil and Durmus, Esin and Gella, Spandana and Stanczak, Karolina and Reddy, Siva},
  booktitle={Forty-second International Conference on Machine Learning},
  year={2025}
}

@article{wu2025mcpmark,
  title={MCPMark: A Benchmark for Stress-Testing Realistic and Comprehensive MCP Use},
  author={Wu, Zijian and Liu, Xiangyan and Zhang, Xinyuan and Chen, Lingjun and Meng, Fanqing and Du, Lingxiao and Zhao, Yiran and Zhang, Fanshi and Ye, Yaoqi and Wang, Jiawei and others},
  journal={arXiv preprint arXiv:2509.24002},
  year={2025}
}
```
