# InfiEpisteme

Automated research pipeline driven by Claude Code. Give it a research direction, and it delivers: a peer-review-quality paper (PDF), clean code repository, and organized experimental results.

**Just talk to Claude Code.** No config files to edit, no scripts to memorize. Describe your research interest, and CC handles everything — from literature search to paper compilation.

## Quick Start

```
You: Clone InfiEpisteme to my GPU server at user@gpu-box and set it up.

CC:  [SSHs to server, clones repo, detects hardware]
     Done. A100-40GB, 216GB RAM, CUDA 12.8. What's your research direction?

You: I want to study Kimi's Attention Residuals paper that just came out.
     Validate it on small LLMs and propose improvements. Target NeurIPS 2026.

CC:  [web-searches the paper, finds competing methods, writes proposal]
     ⚠️ Heads up: this paper is only 2 days old. Semantic Scholar won't have it yet.
     I'll use web search as fallback and broaden to the residual connections field.
     [starts pipeline on server, monitors each stage]

     ...20 min later...

     S1 literature done but only found 21 citations (need 30).
     The regex in state_guard.py doesn't match "et al." format.
     [fixes locally, pushes to GitHub, syncs to server, re-verifies]
     Fixed. 36 citations now. Advancing to S2.

You: What's the status?

CC:  S3 (Implementation) running. Already created 7 model variants:
     PreNorm, AttnRes, DCA, MUDDFormer, Hyper-Connections, DenseFormer, hybrid.

You: Watch the GPU memory during experiments. 0.5B with bf16 should fit.

CC:  Got it. I'll verify batch sizes against hardware_profile.json before S4.
```

That's it. CC handles SSH, configuration, execution, monitoring, debugging, and hotfixing. You steer.

## Setup

**On your GPU server:**
```bash
git clone https://github.com/your-org/InfiEpisteme.git
cd InfiEpisteme
pip install pyyaml requests
claude --version   # Ensure Claude Code is installed
```

**On your local machine:** Just have Claude Code installed. Optionally add MCP servers for enhanced paper search:
```bash
claude mcp add semantic-scholar -- npx -y <semantic-scholar-mcp-package>
```

## Pipeline Stages

```
[Hardware Detection] → P0: Direction Alignment (interactive)
S0: Init → S1: Literature (30+ papers) → S2: Ideation (6-perspective debate)
→ S3: Implementation → S4: Experiments (progressive tree search)
→ S5: Analysis → S6: Paper (LaTeX + citation verification)
→ S7: Review-Revise (cross-model) → S8: Delivery
```

Each stage follows the same cycle: **execute → verify → memory sync → judge → advance**. If a stage fails, the pipeline retries up to 3 times, then pauses for your input.

## How to Use (Conversation Patterns)

### Starting a Project

```
You: My server is user@gpu-box with 2x A100. I want to study [topic].
     Target [venue]. Use [model] for cross-review.

CC:  [sets up server, writes config, runs P0 novelty check]
     Direction looks [Novel/Partially Novel]. Starting pipeline.
```

### Monitoring Progress

```
You: What's the status?
CC:  Currently at S4.2. 4/6 experiment nodes complete. Best result: ...

You: Show me the experiment plan.
CC:  [reads EXPERIMENT_PLAN.md from server and summarizes]

You: What are the risks for this stage?
CC:  S4 risks: budget overrun (67/80 GPU-hours used), OOM on large batch sizes...
```

### Intervening

```
You: H2's direction is wrong. Change it to [new idea].
CC:  [updates experiment_tree.json, resets affected sub-stage, re-runs]

You: The paper needs more recent citations.
CC:  [runs targeted search, adds papers, re-verifies citation count]

You: Stop. I want to change direction entirely.
CC:  [kills processes, resets pipeline to P0]
```

### Debugging

```
CC:  S1 failed: state guard says only 21 citations (need 30).
     Diagnosis: citation regex doesn't match [Author et al., Year] format.
     [fixes locally, pushes, syncs to server, re-verifies]
     6/6 checks passed now.

You: Did you push the fix?
CC:  Yes, commit abc123.
```

### Quick Reference

| You Say | CC Does |
|---------|---------|
| "Run the pipeline on the server" | SSH, configure, start execution |
| "What's the status?" | Read registry.yaml, report progress |
| "What are the risks?" | Analyze topic vs pipeline requirements |
| "Did you push the fix?" | Commit, push to GitHub |
| "Stop, change direction" | Kill processes, reset stage |
| "Continue" | Resume from current stage |

## Architecture

**.md files are the program.** All research logic lives in `skills/*.md` — no framework, no hidden state, fully auditable.

```
run.sh (orchestrator)
  ├── claude -p "skills/S0_hardware.md"              → hardware detection (once)
  ├── claude -p "skills/_common.md + skills/S{N}.md" → execute stage
  ├── scripts/state_guard.py verify                  → validate outputs
  ├── claude -p "skills/memory_sync.md"              → consolidate knowledge
  ├── claude -p "skills/judge.md"                    → quality gate
  └── scripts/state_guard.py advance                 → progress pipeline
```

### Memory System

Each `claude -p` call is stateless. Memory is reconstructed from three layers:

| Layer | Source | Purpose |
|-------|--------|---------|
| State | `registry.yaml`, `experiment_tree.json` | Pipeline position, experiment progress |
| Knowledge | `.ai/core/`, `.ai/evolution/` | Research context, methodology, decisions, negative results |
| Context Chain | `.ai/context_chain.md` | Cross-stage reasoning — the "why" thread |

Skills do NOT update `.ai/` files directly. A dedicated **Memory Synthesizer** runs after every stage to consolidate knowledge, ensuring quality.

### Quality Gates

Every stage must pass three checks before advancing:

1. **State Guard** (deterministic Python) — files exist, citation counts met, fields populated
2. **Memory Sync** — knowledge consolidated into `.ai/`
3. **LLM Judge** — adversarial content quality assessment (checks the work makes scientific sense)

### Cross-Model Review (S7)

The paper written by Claude is reviewed by an external model (GPT-4o/GPT-5.4):

| Reviewer | Model | Focus |
|----------|-------|-------|
| R1 | External | Methods, technical soundness |
| R2 | Internal (Claude) | Clarity, presentation |
| R3 | External | Novelty, contribution |

### Progressive Experiment Tree (S4)

S4 doesn't run one experiment — it searches through a tree of 4 stages:

```
4.1: Preliminary (6 root nodes) → 4.2: Hyperparameter tuning
→ 4.3: Method refinement → 4.4: Ablation studies → RESULTS_SUMMARY.md
```

## Risk Prediction Guide

When supervising cutting-edge research, watch for these:

| Stage | Risk Signal | What to Tell CC |
|-------|------------|-----------------|
| **S1** | Paper < 6 months old | "Semantic Scholar won't have it. Use web search. Broaden to related fields." |
| **S2** | Limited hardware | "Experiments must fit within N GPU-hours." |
| **S3** | No reference code | "Paper has no open-source code. Plan for implementation from scratch." |
| **S4** | Budget overrun | "Monitor GPU usage. Stop early if approaching budget." |
| **S6** | Citation issues | "Check citation count and format — we've seen regex mismatches before." |
| **S7** | API key missing | "Confirm OPENAI_API_KEY is set for cross-review." |

## Configuration

All done through conversation with CC, or edit `config.yaml` directly:

```yaml
research_direction: "your research question"
target_venue: "NeurIPS 2026"
target_score: 6.0                    # minimum reviewer score

compute:
  gpu_hours: 100
  gpu_type: "A100"
  parallel_jobs: 3

cross_review:
  enabled: true
  model: "gpt-4o"                    # or "gpt-5.4"
  api_key_env: "OPENAI_API_KEY"
```

## What It Produces

```
DELIVERY/
  paper.pdf               # Peer-review-quality paper
  code/src/               # Clean implementation
  code/requirements.txt
  results/                # Full experiment tree with metrics and figures
  reviews/                # All reviewer feedback across cycles
  DELIVERY.md             # Summary for human review
```

## Safety Mechanisms

| Mechanism | Purpose |
|-----------|---------|
| Circuit breaker | Same failure 3x → pipeline pauses for human |
| GPU budget check | Flags experiments exceeding compute budget |
| Judge gate | Every stage must pass LLM-as-judge |
| Citation verification | 5-step protocol eliminates ~40% LLM citation error rate |
| Git pre-registration | Experiment design committed before execution |
| Hardware detection | Prevents experiments exceeding GPU/RAM capacity |
| Venue checklists | NeurIPS/ICML/ICLR/ACL-specific checks before delivery |

## Acknowledgments

- [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) — cross-model review, state-persistent loops
- [Sibyl](https://github.com/Sibyl-Research-Team/sibyl-research-system) — multi-perspective debate, self-healing
- [GPT-Researcher](https://github.com/assafelovic/gpt-researcher) — multi-source aggregation
- [AgentInfra](https://github.com/JayCheng113/AgentInfra) — .ai/ persistent knowledge layer
- [Orchestra Research](https://github.com/orchestra-research/ai-research-skills) — citation verification, venue checklists

## License

MIT
