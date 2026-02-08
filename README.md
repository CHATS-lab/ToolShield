# Unsafer in Many Turns: Benchmarking and Defending Multi-Turn Safety Risks in Tool-Using Agents

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/📄_Paper-Coming_Soon-gray" alt="Paper"></a>
<a href="https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk"><img src="https://img.shields.io/badge/🤗_Dataset-HuggingFace-yellow" alt="Dataset"></a>
<a href="https://unsafer-in-many-turns.github.io"><img src="https://img.shields.io/badge/🌐_Website-Project_Page-blue" alt="Website"></a>
<a href="https://www.notion.so/Unsafer-in-Many-Turns-Benchmarking-and-Defending-Multi-Turn-Safety-Risks-in-Tool-Using-Agents-30102b8c305b80dfb65de3cec21db4a3?source=copy_link"><img src="https://img.shields.io/badge/📝_Blog-Notion-black" alt="Blog"></a>
</p>

This repository contains the code and data for **MT-AgentRisk**, a benchmark for evaluating multi-turn safety in tool-using agents, and **ToolShield**, a training-free defense that leverages the agent's own capabilities to improve safety awareness.

## Overview
<p align="center">
  <img src="overview.jpg" alt="Overview" style="width: 75%;">
</p>

The safety-capability gap in LLM-based agents widens as they engage in multi-turn interactions and employ diverse tools, introducing risks overlooked by existing benchmarks. This work addresses this gap with:

1. **A principled attack taxonomy** that transforms single-turn harmful tasks into multi-turn attack sequences across three dimensions: Format, Method, and Target.

2. **MT-AgentRisk Benchmark**: 365 single-turn harmful tasks across five tools (Filesystem-MCP, Browser/Playwright-MCP, PostgreSQL-MCP, Notion-MCP, Terminal), transformed into multi-turn attack sequences using our taxonomy, ASR increase by 16% on avg.

3. **ToolShield Defense**: A training-free, tool-agnostic defense where agents explore tool functionality in a sandbox, learn from their own executions, and distill safety experiences before deployment. ToolShield reduces ASR by 30% on avg.

## Repository Layout
```
./
├── workspaces/                              # MT-AgentRisk: multi-turn tool-agent safety benchmark
│   ├── single_turn_tasks/                   # Single-turn tasks 
│   │   └── <tool>/                          
│   │       └── <task_name>/
│   │           ├── task.md                  # Instruction shown to the agent
│   │           ├── workspace/               # Pre-seeded sandbox filesystem contents
│   │           └── utils/
│   │               └── dependencies.yml     # MCP/tools required by this task
│   ├── multi_turn_tasks/                    # Multi-turn tasks
│   │   └── <tool>/
│   │       └── <task_name>/
│   │           ├── turns.yml                # Turn manifest (order, patterns)
│   │           ├── task-turn-*.md           # Per-turn instructions
│   │           ├── workspace/               # Pre-seeded contents
│   │           └── utils/
│   │               └── dependencies.yml
├── evaluation/                              # Task execution
│   ├── run_eval.py                          # Main runner
│   ├── post_eval.py                         # LLM-as-judge
│   ├── run_together.sh                     
│   ├── agent_config/                        # Agent LLM configurations
│   │   └── config_model.toml
│   └── README.md
└── self_exploration (ToolShield)/           # ToolShield: self-exploration defense pipeline
    ├── tree_generation.py                   # Generates safety trees + test case bundles
    ├── iterative_exp_runner.py              # Iterative experience generation
    ├── prompts.py                           
    ├── post_process_prompts.py              
    └── toolshield.py                        # main file for defense
```

## Quick Start

### 1. Environment Preparation

#### 1.1 Download Dataset

Download the benchmark data from [HuggingFace](https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk):
```bash
git clone https://huggingface.co/datasets/CHATS-Lab/MT-AgentRisk
cp -r MT-AgentRisk/workspaces/* workspaces/
```

#### 1.2 Setup OpenHands
```bash
git clone --branch 0.54.0 --single-branch https://github.com/OpenHands/OpenHands.git
cp MT-AgentRisk_ToolShield/evaluation/client.py OpenHands/openhands/mcp/client.py
cd MT-AgentRisk_ToolShield && poetry install
```

#### 1.3 Clone MCPMark
```bash
git clone https://github.com/eval-sys/mcpmark.git MT-AgentRisk_ToolShield/mcpmark-main
```

> 📝 Follow [this guide](https://github.com/eval-sys/mcpmark/blob/main/docs/mcp/notion.md) to get your `NOTION_TOKEN`.

#### 1.4 Pull Docker Images
```bash
# TODO: Add our Docker Hub images
```
> 📝 **Playwright Note**: The current setup supports partial Playwright functionality. To enable full Playwright with Reddit, Shopping, and Shopping Admin, follow the [SafeArena setup guide](https://github.com/McGill-NLP/safearena/blob/main/README.md). See MT-AgentRisk_ToolShield/evaluation/playwright_note/README.md for integration instructions.

#### 1.5 Env Vars && Start MCP Servers
```bash
export TOOLSHIELD_MODEL_NAME="anthropic/claude-sonnet-4.5"
export OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
export NOTION_TOKEN="YOUR_EVAL_NOTION_KEY"
export SOURCE_NOTION_KEY="YOUR_SOURCE_NOTION_KEY"
export SERVER_HOST="localhost"  # Change to your server address if needed

bash MT-AgentRisk_ToolShield/evaluation/start_mcp_servers.sh
```

> ⚠️ When setting `TOOLSHIELD_MODEL_NAME`, **do not** include the `openrouter/` prefix.

This will start all required MCP services (Notion, Filesystem, etc.) in the background.

---

### 2. Running ToolShield Defense (Self-Exploration)

This runs the full ToolShield pipeline: **Inspect MCP → Generate Safety Tree → Generate Tests → Distill Experiences → Inject into Agent Context**.
```bash
python self_exploration/toolshield.py \
  --mcp_name postgres \
  --mcp_server http://localhost:9091 \
  --output_path /mnt/data/MT-AgentRisk_ToolShield/self_exploration/exp_examples \
  --agent codex
```

#### Output

The experience file is saved as:
```
<output_path>/../experience_list_{model_name}_{tool}.json
```
and it will append to specified agents' context automatically.

For more details, see `MT-AgentRisk_ToolShield/self_exploration/README.md`.

---

### 3. Running Evaluation on MT-AgentRisk

Use `evaluation/run_eval.py` to evaluate agents on tasks.

#### Agent Configuration

Agent configurations are defined in TOML files under `evaluation/agent_config/`:
```toml
# Example: evaluation/agent_config/config.toml
[llm.agent]
model = "openrouter/anthropic/claude-sonnet-4.5"
base_url = "https://openrouter.ai/api/v1"
api_key = ""

[llm.env]
model = "openrouter/anthropic/claude-sonnet-4.5"
base_url = "https://openrouter.ai/api/v1"
api_key = ""
```

#### Run a Single Task
```bash
poetry run python evaluation/run_eval.py \
  --task-path workspaces/terminal/multi_turn_tasks/multi-turn_root-remove \
  --agent-llm-config agent \
  --env-llm-config env \
  --outputs-path evaluation/test_output \
  --use-experience experience.json \
  --server-hostname localhost
```

Remove the "--use-experience" to run evaluation without defense.

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

---

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