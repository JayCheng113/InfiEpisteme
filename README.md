# InfiEpisteme

> **Talk to Claude Code. Get a research paper.**

InfiEpisteme is an automated research pipeline that turns a research idea into a peer-review-quality paper, clean code, and organized results — all through natural language conversation with Claude Code.

No frameworks to learn. No scripts to memorize. Just describe what you want to study.

```
You: I want to study Kimi's Attention Residuals paper that just came out.
     Validate it on small LLMs and propose improvements. Target NeurIPS 2026.

CC:  [searches web, finds paper, identifies 5 competing methods]
     [sets up server, writes proposal, starts 9-stage pipeline]
     [pauses for your review at key decisions]
     [monitors, catches bugs, fixes them, keeps going]

     ...6 hours later...

     Pipeline complete. Paper: 12 pages, 36 citations, 6 experiments.
     → DELIVERY/paper.pdf
```

## Why InfiEpisteme?

| Traditional | InfiEpisteme |
|-------------|-------------|
| Edit YAML configs | Just talk |
| Read docs to learn the framework | CC already knows how |
| SSH in to debug when things break | CC diagnoses and fixes automatically |
| Monitor scripts manually | CC watches for risks proactively |
| Restart from scratch on failure | CC retries, hotfixes, resumes |

**Key advantage**: You command one local Claude Code, which commands multiple Claude Code instances on the server — and actively monitors, diagnoses, and hotfixes along the way.

## Self-Evolving Pipeline

InfiEpisteme improves itself through natural language — no RL, no retraining, just updated instructions.

```
     Run pipeline
          │
          ▼
     Observe problems ◄─── "S1 only found 21 citations, need 30"
          │
          ▼
     Discuss with CC  ◄─── "The regex doesn't match 'et al.' format"
          │
          ▼
     CC updates .md   ◄─── S1_literature.md: "Web Search is Source 1, not fallback"
          │                 state_guard.py: fix regex
          ▼                 S2_ideation.md: "speculative hypotheses must be questions"
     Next run is better
          │
          └──► repeat
```

Every skill file is a natural language instruction. When something goes wrong, you tell CC what happened, and it rewrites the instruction to prevent the same mistake. Real examples from our first run:

| You said | CC improved |
|----------|------------|
| "Why only 21 citations?" | S1: Web Search promoted to primary source; added "run second pass if < 30" |
| "This hypothesis has no evidence" | S2: Added `evidence_basis: speculative` label requirement |
| "The node packed 6 training runs" | S2: Added "one node = one training run" rule |
| "500M tokens is too much for preliminary" | S4: Added "S4.1 uses 100-200M tokens" limit |
| "experiment_tree.json never updates" | S4: Added "set status to running BEFORE training" step |
| "Only one architecture isn't convincing" | Added Pythia arch support; redesigned S4.1 as cross-architecture screening |
| "Training restarted and lost 2h of logs" | S4/common: Added "never overwrite results, back up with timestamp" rule |

**The pipeline's instructions are its weights. Natural language is the gradient. Conversation is the training loop.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  You: "Study Attention Residuals, target NeurIPS 2026"                     │
│   │                                                                        │
│   ▼                                                                        │
│  Local Claude Code (mission control — the only CC you talk to)             │
│   │                                                                        │
│   ├─ Web search: finds paper, competing methods                            │
│   ├─ SSH: configures server, writes config.yaml                            │
│   │                                                                        │
│   │  ┌─ Per-stage execution loop ─────────────────────────────────────┐    │
│   │  │                                                                 │    │
│   │  │  ssh: claude -p "skills/S{N}.md"     ──► skill execution       │    │
│   │  │  ssh: state_guard.py verify          ──► deterministic check   │    │
│   │  │  ssh: claude -p "skills/memory_sync" ──► knowledge consolidate │    │
│   │  │  ssh: claude -p "skills/judge.md"    ──► 3-layer quality gate  │    │
│   │  │       Layer 1: deterministic checks                            │    │
│   │  │       Layer 2: content quality                                 │    │
│   │  │       Layer 3: first-principles reasoning                     │    │
│   │  │  ssh: state_guard.py advance         ──► next stage or retry  │    │
│   │  │                                                                 │    │
│   │  │  [CHECKPOINT at P0, S2, S3?] ──► pause for human review       │    │
│   │  │       Fixed checklist (targets known failure modes)            │    │
│   │  │       + LLM adversarial brief (supplements)                   │    │
│   │  │       + Raw file access (fallback)                            │    │
│   │  │       ──► ./run.sh approve to continue                        │    │
│   │  │                                                                 │    │
│   │  └────────────────────────────────────────────────────────────────┘    │
│   │                                                                        │
│   ├─ Diagnoses failures, hotfixes, retries automatically                   │
│   ├─ Reports to you in plain language                                      │
│   └─ Repeats for all stages ─── intervene anytime ◄── You                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

GPU Server receives SSH commands. Each "claude -p" spawns an independent
CC instance that reads skill instructions, does the work, writes files.
Local CC checks results, decides next action.
```

**`run.sh` is optional.** It automates the loop for unattended runs, but the real orchestrator is your local Claude Code. In practice, local CC provides better results because it can:

- **Predict risks** before they happen ("this paper is too new for Semantic Scholar")
- **Diagnose root causes** when checks fail ("regex doesn't match this citation format")
- **Hotfix and retry** without waiting for 3 automated failures
- **Search the web** for context that server-side CC can't access
- **Report to you** in plain language and ask for judgment calls

**The chain of command**: You give one instruction in natural language → your local CC breaks it into actions → each action spawns a dedicated CC instance on the server → they coordinate through shared files → local CC monitors results and intervenes when needed.

### .md Files Are the Program

All research logic lives in `skills/*.md` files — structured markdown that Claude Code executes natively. No framework overhead, no hidden state. Every decision traces back to a readable `.md` file.

### Three-Layer Memory

Each `claude -p` call is stateless. Memory is reconstructed from files:

```
Layer 1: State         registry.yaml, experiment_tree.json
Layer 2: Knowledge     .ai/core/ (research context, methodology, literature)
                       .ai/evolution/ (decisions, negative results, experiment log)
Layer 3: Context       .ai/context_chain.md — the "why" thread across stages
```

A dedicated Memory Synthesizer runs after every stage to consolidate knowledge. Skills never write to `.ai/` directly.

## Setup

### Prerequisites

- **Local machine**: [Claude Code](https://claude.com/claude-code) installed
- **GPU server**: SSH access to a machine with GPU (e.g., `ubuntu@gpu-box`)
  - Claude Code installed on the server
  - Python 3.10+ with `pyyaml`, `requests`
  - OpenAI API key on the server (for cross-model review in S7):
    ```bash
    echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc && source ~/.bashrc
    ```

### Server Setup

Clone and configure on the server:
```bash
ssh user@gpu-box
git clone https://github.com/JayCheng113/InfiEpisteme.git
cd InfiEpisteme
pip install pyyaml requests
```

Then edit `config.yaml` on the server:
```yaml
research_direction: |
  Your research idea here. Be specific: what problem, what method,
  what comparison, what scale. The more detail, the better the pipeline
  performs. Example:
  "Validate Kimi's Attention Residuals on dense sub-2B LLMs.
   Compare against DCA, MUDDFormer, DenseFormer on LLaMA and Pythia
   at 0.5B scale. Target NeurIPS 2026."

target_venue: "NeurIPS 2026"    # or "ICML 2026", "arxiv", etc.

compute:
  gpu_hours: 80                  # your available GPU budget
  gpu_type: "A100"               # your GPU type
  parallel_jobs: 1               # how many experiments to run at once
```

### Two Ways to Run

**Option A: Interactive (recommended)** — You talk to your local Claude Code, it SSHs to the server and runs stages one by one. You can monitor, intervene, and guide at any point.

```
You: SSH to ubuntu@gpu-box, go to ~/InfiEpisteme, and start the research pipeline.
```

Your local CC will read config.yaml, run each stage via `claude -p`, check results, and report back. At checkpoints (P0, S2, and conditionally S3 for novel methods), it pauses for your review.

**Option B: Unattended** — Run directly on the server:
```bash
./run.sh start                        # runs pipeline, pauses at checkpoints
./run.sh approve                      # approve checkpoint and continue
./run.sh approve --with 'add Pythia'  # approve with modifications
./run.sh status                       # check progress
```

## How It Works in Practice

### 1. You describe your research idea

The most important input is `config.yaml`'s `research_direction`. Write it yourself, or tell your local CC what you want and ask it to write config.yaml for you:

```
You: I want to study Kimi's Attention Residuals paper (arxiv:2603.15031).
     Validate it on small dense LLMs, compare against other depth-aggregation
     methods, and propose improvements. Target NeurIPS 2026. I have an A100-40GB
     with 80 GPU-hours budget.

CC:  Got it. I'll write config.yaml with this direction and set up the pipeline.
     [SSHs to server, writes config.yaml, starts P0]
```

### 2. Pipeline runs, pauses at checkpoints

```
     ── CHECKPOINT: P0 (research direction) ──
     CC:  Here's the formalized proposal. Please verify:
          1. Is the hypothesis correctly framed?
          2. Is the scope appropriate for NeurIPS?
          3. Is the compute budget feasible?

You: Looks good, but add DHC as a baseline too.
CC:  [updates proposal, continues to S1-S2]

     ── CHECKPOINT: S2 (experiment design) ──
     CC:  Experiment design ready. 14 nodes, 2 architectures. Check:
          1. Each node tests exactly one variable? ✓
          2. Budget: 14 × 2.5h = ~35h screening. Leaves 45h for tuning. ✓
          3. Any missing baselines?

You: Go.
CC:  [runs S3, implements all methods]

     ── CHECKPOINT: S3 (only if you proposed a novel method) ──
     CC:  Implementation complete. Your DPE-AttnRes method:
          - depth_scale initialized at 0.01 (learnable, ReZero-style)
          - Invariant verified: reduces to vanilla AttnRes when scale=0 ✓
          - 341.9M params, 14.5 GB peak memory
          Approve to start training?

You: Go.
CC:  [runs S4-S8 fully automated, reports when done]
```

### 3. Monitor anytime

```
You: What's the status?
CC:  S4.2 running. 4/6 experiments complete. Best perplexity: 48.4.

You: Change H2's direction to [new idea].
CC:  [updates experiment tree, re-runs affected sub-stage]
```

### 4. CC handles problems automatically

```
CC:  S1 failed: only 21 citations detected (need 30).
     Root cause: regex doesn't match "et al." format.
     [fixes regex, re-verifies]
     Fixed. 36 citations now. Advancing.
```

## Pipeline Stages

```
P0 → [CHECKPOINT] → S0 → S1 → S2 → [CHECKPOINT] → S3 → [CHECKPOINT?] → S4 → S5 → S6 → S7 → S8
 │                                │                  │                           │
 direction                    experiment          fully automated            delivery
 (human reviews)              design              (code, train,
                              (human reviews)      analyze, write,
                                                   review, package)
```

| Stage | What Happens | Output |
|-------|-------------|--------|
| **P0** | You + CC brainstorm direction, novelty check | `RESEARCH_PROPOSAL.md` |
| | **[CHECKPOINT]** — human reviews direction, checks factual claims | |
| **S0** | Hardware detection, init .ai/ knowledge base | `hardware_profile.json`, `.ai/` |
| **S1** | Literature survey (30+ papers, multi-source) | `RELATED_WORK.md`, `BASELINES.md`, `bibliography.bib` |
| **S2** | 6-perspective hypothesis debate, experiment design | `EXPERIMENT_PLAN.md`, `experiment_tree.json` |
| | **[CHECKPOINT]** — human reviews design, verifies budget, checks baselines | |
| **S3** | Implement methods + baselines | `src/`, `requirements.txt` |
| | **[CHECKPOINT?]** — triggers if novel methods exist; human reviews implementation details | |
| **S3** | Implement methods + baselines | `src/`, `requirements.txt` |
| **S4** | Progressive tree search (4 sub-stages, 6+ experiments) | `RESULTS_SUMMARY.md`, `results/` |
| **S5** | Statistical analysis, 6-perspective interpretation | `ANALYSIS.md`, `tables/`, `figures/` |
| **S6** | LaTeX paper with 5-step citation verification | `paper.pdf` |
| **S7** | Cross-model adversarial review (Claude writes, GPT reviews) | `reviews/` |
| **S8** | Package deliverables, venue-specific checklist | `DELIVERY/` |

**10 stages (P0 + S0-S8), 2-3 need human input** (P0, S2, and S3 if you proposed a novel method). The rest run fully automated.

## Safety & Quality

| Mechanism | What It Does |
|-----------|-------------|
| **Human checkpoints** | Pipeline pauses after P0, S2, and conditionally S3 (novel methods) for human review — fixed checklist + LLM adversarial brief + raw file access |
| **3-Layer Judge** | Layer 1: deterministic checks. Layer 2: content quality. Layer 3: first-principles reasoning — challenges assumptions, catches factual errors, flags insufficient experimental design |
| **Circuit breaker** | Same failure 3x → pauses for human input |
| **State Guard** | Deterministic Python checks after every stage |
| **Citation verification** | 5-step protocol — every citation verified in 2+ sources |
| **Cross-model review** | External model (GPT) reviews the paper Claude wrote |
| **Hardware detection** | Prevents experiments exceeding GPU/RAM capacity |
| **Git pre-registration** | Experiment design committed before execution |
| **Venue checklists** | NeurIPS/ICML/ICLR/ACL-specific checks before delivery |

## 3-Layer Judge in Action

Every stage passes through a judge before advancing. The judge doesn't just check boxes — it reasons from first principles.

```
S2 just completed. Judge evaluating...

Layer 1 (deterministic):
  ✓ EXPERIMENT_PLAN.md exists
  ✓ experiment_tree.json has 8 nodes
  ✓ Each node has id, approach, success_metric

Layer 2 (content quality):
  ✓ Hypotheses are genuinely different
  ✓ Multi-perspective debate includes real criticism
  ✗ Baseline list missing DenseFormer — important competitor

Layer 3 (first-principles):
  ✗ "All experiments use LLaMA only. A benchmark claim at NeurIPS
     requires ≥2 architectures to demonstrate generalizability."
  ✗ "H3 states 'AttnRes underperforms on dense models' as fact,
     but evidence_basis is speculative. Reframe as question."
  ⚠ "Budget: 16 nodes × 500M tokens = 43 GPU-hours for screening
     alone. 200M tokens would suffice and leave room for ablations."

Result: RETRY
Guidance: "Add second architecture (e.g., Pythia). Reframe H3 as
question. Reduce screening to 200M tokens."
```

Without Layer 3, this stage would have passed — the files exist, the counts are right. But the research design had fundamental problems that would have wasted 43 GPU-hours and produced a paper no reviewer would accept.

## Risk Prediction

When working on cutting-edge topics, CC proactively watches for:

| Risk | CC's Response |
|------|--------------|
| Paper too new for Semantic Scholar | Falls back to web search, broadens to related fields |
| Not enough papers for 30-citation threshold | Supplements with adjacent literature |
| Experiments exceed GPU budget | Adjusts batch size, reduces model scale, or stops early |
| Citation format mismatch | Fixes validation regex, re-verifies |
| API errors mid-pipeline | Retries with exponential backoff, or resumes from checkpoint |

**Optional MCP servers** for enhanced paper search:
```bash
claude mcp add semantic-scholar -- npx -y <semantic-scholar-mcp-package>
```

## What It Produces

```
DELIVERY/
  paper.pdf                 # Peer-review-quality paper
  code/src/                 # Clean implementation
  code/requirements.txt     # Dependencies
  results/                  # Experiment tree, metrics, figures
  reviews/                  # All reviewer feedback
  DELIVERY.md               # Summary for human review
```

## Acknowledgments

Design informed by:
- [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) — cross-model review, state-persistent loops
- [Sibyl](https://github.com/Sibyl-Research-Team/sibyl-research-system) — multi-perspective debate, self-healing
- [GPT-Researcher](https://github.com/assafelovic/gpt-researcher) — multi-source aggregation
- [AgentInfra](https://github.com/JayCheng113/AgentInfra) — .ai/ persistent knowledge layer
- [Orchestra Research](https://github.com/orchestra-research/ai-research-skills) — citation verification, venue checklists
- [LaTeX Document Skill](https://github.com/ndpvt-web/latex-document-skill) — LaTeX debugging patterns, long-form best practices
- [Academic Writing Skills](https://github.com/bahayonghang/academic-writing-skills) — academic style guide, common writing errors
- [Antigravity Awesome Skills](https://github.com/sickn33/antigravity-awesome-skills) — incremental build-verify, coding practices, TDD principles

## License

MIT
