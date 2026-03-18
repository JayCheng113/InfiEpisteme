# InfiEpisteme

> **Talk to Claude Code. Get a research paper.**

InfiEpisteme is an automated research pipeline that turns a research idea into a peer-review-quality paper, clean code, and organized results — all through natural language conversation with Claude Code.

No frameworks to learn. No config files to edit. No scripts to memorize. Just describe what you want to study.

```
You: I want to study Kimi's Attention Residuals paper that just came out.
     Validate it on small LLMs and propose improvements. Target NeurIPS 2026.

CC:  [searches web, finds paper, identifies 5 competing methods]
     [sets up server, writes proposal, starts 9-stage pipeline]
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

InfiEpisteme improves itself through natural language — no RL, no code rewrites, no retraining.

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

**The pipeline's instructions are its weights. Natural language is the gradient. Conversation is the training loop.**

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   You: "Study Attention Residuals, target NeurIPS 2026"                │
│    │                                                                   │
│    ▼                                                                   │
│   Local Claude Code ◄──────────────────────────────────────────┐      │
│    │  (mission control — the only CC you talk to)              │      │
│    │                                                            │      │
│    ├─ Web search: finds paper, competing methods               │      │
│    ├─ Risk analysis: "paper is 2 days old, S1 will struggle"   │      │
│    ├─ SSH: configures server, writes config.yaml               │      │
│    │                                                            │      │
│    │   ┌─ Executes stage ──────────────────────────────┐       │      │
│    │   │                                                │       │      │
│    ├───┼─ ssh: claude -p "skills/S1.md" ───────────────┼──►[1] │      │
│    │   │  (spawns CC instance on server for skill)      │       │      │
│    │   │                                                │       │      │
│    ├───┼─ ssh: state_guard.py verify ──────────────────┼──►[2] │      │
│    │   │  (deterministic check — no CC needed)          │       │      │
│    │   │                                                │       │      │
│    │   │  ◄── FAIL: "only 21 citations, need 30"       │       │      │
│    │   │                                                │       │      │
│    ├─ Diagnoses: "regex doesn't match 'et al.' format" │       │      │
│    ├─ Fixes state_guard.py locally                      │       │      │
│    ├─ git push + rsync to server                        │       │      │
│    ├─ Runs supplement search for more papers            │       │      │
│    │   │                                                │       │      │
│    ├───┼─ ssh: state_guard.py verify ──────────────────┼──►[3] │      │
│    │   │  ◄── PASS: 36 citations                        │       │      │
│    │   │                                                │       │      │
│    ├───┼─ ssh: claude -p "skills/judge.md" ────────────┼──►[4] │      │
│    │   │  (spawns CC instance for quality evaluation)   │       │      │
│    │   │                                                │       │      │
│    ├───┼─ ssh: state_guard.py advance ─────────────────┼──►[5] │      │
│    │   │  ◄── "PASSED — advanced to S2"                 │       │      │
│    │   └────────────────────────────────────────────────┘       │      │
│    │                                                            │      │
│    ├─ Reports to you: "S1 done, 36 papers. Starting S2."  ─────┘      │
│    │                                                                   │
│    └─ Repeats for S2, S3, S4... ─── intervene anytime ◄── You        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

GPU Server receives SSH commands. Each "claude -p" spawns an independent
CC instance that reads skill instructions, does the work, writes files.
Local CC checks results, decides next action. No run.sh required.
```

**`run.sh` is optional.** It automates the loop for unattended runs, but the real orchestrator is your local Claude Code. In practice, local CC provides better results because it can:

- **Predict risks** before they happen ("this paper is too new for Semantic Scholar")
- **Diagnose root causes** when checks fail ("regex doesn't match this citation format")
- **Hotfix and retry** without waiting for 3 automated failures
- **Search the web** for context that server-side CC can't access
- **Report to you** in plain language and ask for judgment calls

**The chain of command**: You give one instruction in natural language → your local CC breaks it into actions → each action spawns a dedicated CC instance on the server (one for the skill, one for memory sync, one for judging) → they coordinate through shared files → local CC monitors results and intervenes when needed.

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

## How to Use

### Getting Started

```
You: My server is user@gpu-box with an A100. Clone InfiEpisteme and set it up.
CC:  [SSHs to server, clones, detects hardware] Done. What's your research direction?

You: [describe your research idea in plain language]
CC:  [searches literature, checks novelty, writes proposal, starts pipeline]
```

### Monitoring

```
You: What's the status?
CC:  S4.2 running. 4/6 experiments complete. Best accuracy: 87.2%.

You: What are the risks for this stage?
CC:  Paper is only 2 days old — Semantic Scholar won't have it. I'm using web search.
```

### Intervening

```
You: Change H2's direction to [new idea].
CC:  [updates experiment tree, re-runs affected sub-stage]

You: Stop. I want a completely different topic.
CC:  [kills processes, resets to P0, waits for your new direction]
```

### Debugging (CC does this automatically)

```
CC:  S1 failed: only 21 citations detected (need 30).
     Root cause: regex doesn't match "et al." format.
     [fixes locally, pushes to GitHub, syncs to server, re-verifies]
     Fixed. 36 citations now. Advancing.
```

## Pipeline Stages

| Stage | What Happens | Output |
|-------|-------------|--------|
| **P0** | You + CC brainstorm direction, novelty check | `RESEARCH_PROPOSAL.md` |
| **S0** | Hardware detection, init .ai/ knowledge base | `hardware_profile.json`, `.ai/` |
| **S1** | Literature survey (30+ papers, multi-source) | `RELATED_WORK.md`, `BASELINES.md`, `bibliography.bib` |
| **S2** | 6-perspective hypothesis debate, experiment design | `EXPERIMENT_PLAN.md`, `experiment_tree.json` |
| **S3** | Implement methods + baselines | `src/`, `requirements.txt` |
| **S4** | Progressive tree search (4 sub-stages, 6+ experiments) | `RESULTS_SUMMARY.md`, `results/` |
| **S5** | Statistical analysis, 6-perspective interpretation | `ANALYSIS.md`, `tables/`, `figures/` |
| **S6** | LaTeX paper with 5-step citation verification | `paper.pdf` |
| **S7** | Cross-model adversarial review (Claude writes, GPT reviews) | `reviews/` |
| **S8** | Package deliverables, venue-specific checklist | `DELIVERY/` |

## Safety & Quality

| Mechanism | What It Does |
|-----------|-------------|
| **Circuit breaker** | Same failure 3x → pauses for human input |
| **State Guard** | Deterministic Python checks after every stage |
| **LLM Judge** | Adversarial quality assessment before advancing |
| **Citation verification** | 5-step protocol — every citation verified in 2+ sources |
| **Cross-model review** | External model (GPT) reviews the paper Claude wrote |
| **Hardware detection** | Prevents experiments exceeding GPU/RAM capacity |
| **Git pre-registration** | Experiment design committed before execution |
| **Venue checklists** | NeurIPS/ICML/ICLR/ACL-specific checks before delivery |

## Risk Prediction

When working on cutting-edge topics, CC proactively watches for:

| Risk | CC's Response |
|------|--------------|
| Paper too new for Semantic Scholar | Falls back to web search, broadens to related fields |
| Not enough papers for 30-citation threshold | Supplements with adjacent literature |
| Experiments exceed GPU budget | Adjusts batch size, reduces model scale, or stops early |
| Citation format mismatch | Fixes validation regex, re-verifies |
| API errors mid-pipeline | Retries, or resumes from last checkpoint |

## Setup

**GPU Server** (one-time):
```bash
git clone https://github.com/your-org/InfiEpisteme.git && cd InfiEpisteme
pip install pyyaml requests
claude --version   # Claude Code must be installed
```

**Local Machine**: Just have Claude Code installed. Then start a conversation.

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

## License

MIT
