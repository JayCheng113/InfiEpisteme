---
name: Architecture
description: "System architecture of the InfiEpisteme v2 .md-native research pipeline"
layer: core
last_updated: 2026-03-16
---

# Architecture (v2)

## Overview

InfiEpisteme is an automated research pipeline where **.md files are the program**. Claude Code executes skill files directly via `claude -p`. Python exists only for tasks .md genuinely cannot do (GPU submission, external API calls, state validation).

## System Diagram

```
run.sh (bash loop)
  ├── claude -p "skills/S0_hardware.md" → hardware detection (once at start)
  ├── scripts/parse_state.py → read registry.yaml
  ├── claude -p "skills/_common.md + skills/S{N}.md" → execute stage
  │     └── MCP tools (preferred) → fallback to Python scripts
  ├── scripts/state_guard.py verify → validate + repair state
  ├── claude -p "skills/memory_sync.md" → memory consolidation
  ├── scripts/state_guard.py verify → validate memory quality
  ├── claude -p "skills/judge.md" → LLM-as-judge quality gate
  ├── scripts/state_guard.py advance → advance or retry
  └── loop until COMPLETE or failure

User → Phase 0 (Direction Alignment, ~30min)
         ↓ RESEARCH_PROPOSAL.md locked
       Phase 1 (Fully Unattended)
         S0: Init → S1: Literature → S2: Ideation → S3: Code →
         S4: Experiments (tree search) → S5: Analysis →
         S6: Writing → S7: Review-Revise → S8: Delivery
         ↓
       DELIVERY/ (paper.pdf + code/ + results/)
```

## Components

### Pipeline Driver (`run.sh`)
Bash loop: reads registry.yaml, dispatches skills, runs state guard and judge, advances stages. ~80 lines.

### Skills (`skills/`)
17 .md files — Claude Code native execution. Each is a complete instruction set:
- `_common.md` — shared preamble (state loading, anti-hallucination rules)
- `P0_clarification.md`, `P0_novelty.md` — Phase 0 (interactive)
- `S0_init.md` through `S8_delivery.md` — pipeline stages
- `memory_sync.md` — **Memory Synthesizer**: runs after every stage, consolidates knowledge into .ai/ (executing skills do NOT update .ai/ — this skill does)
- `judge.md` — LLM-as-judge (two-layer: deterministic + content quality)
- `vlm_review.md` — VLM figure quality gate

### State Guardian (`scripts/state_guard.py`)
Deterministic Python that validates + repairs state after each skill execution. Ensures pipeline integrity even when Claude Code misses state updates. ~150 lines.

### MCP Integration (v2.1)
Three core MCP servers provide tool access, with Python script fallbacks:

| MCP Server | Purpose | Fallback |
|------------|---------|----------|
| `semantic-scholar` | Paper search, details, citations | `scripts/scholarly_search.py` |
| `system-monitor` | CPU/GPU/RAM/disk detection | `nvidia-smi`, `psutil` |
| `ssh` | Remote GPU job submission/polling | `scripts/gpu_submit.py`, `scripts/gpu_poll.py` |

Install: `claude mcp add <name> -- npx -y <package>`

### Hardware Detection (v2.1)
`skills/S0_hardware.md` runs once at pipeline start, producing `hardware_profile.json`. All downstream skills adapt experiment plans, batch sizes, and parallelism to actual hardware capabilities.

### Python Scripts (`scripts/`)
Minimal CLI tools, now serving as fallbacks when MCP is unavailable:
- `gpu_submit.py` / `gpu_poll.py` — GPU job management (local + SLURM)
- `cross_review.py` — external model review dispatch (GPT-4o/Gemini)
- `scholarly_search.py` — Semantic Scholar API
- `parse_state.py` / `update_state.py` — YAML read/write

### State Machine (`PIPELINE.md`)
Declarative stage definitions: expected outputs, judge criteria, timeouts, retries. Read by `state_guard.py` for verification.

### Memory Layer (`.ai/` + `context_chain.md`)
Knowledge persists across stateless `claude -p` sessions via file-based memory:
- `.ai/core/` — curated summaries (research-context, methodology, literature)
- `.ai/evolution/` — append-only logs (decisions, negative-results, experiment-log)
- `.ai/context_chain.md` — running reasoning chain: each stage records what/why/what-next
- `memory_sync.md` consolidates after each stage; `state_guard.py` validates content quality

### State Files
- `registry.yaml` — pipeline position + per-stage status/attempts
- `hardware_profile.json` — detected hardware capabilities (GPU, CPU, RAM, disk)
- `experiment_tree.json` — experiment tree with node states
- `state/JUDGE_RESULT.json` — latest judge evaluation
- `state/MEMORY_SYNC_RESULT.json` — memory consolidation report
- `state/REVIEW_STATE.json` — S7 review cycle tracking
- `state/GPU_JOBS.json` — active GPU jobs

## Key Design Decisions

1. **.md is the program** — all logic in skill files, not Python orchestrator
2. **State Guardian** — deterministic Python validates state after each LLM execution
3. **Tree search over linear execution** — experiments branch and compete (S4)
4. **Cross-model adversarial review** — Claude writes, GPT-4o reviews (eliminates self-review bias)
5. **Multi-perspective debate** — 6 viewpoints for ideation (S2) and analysis (S5), from Sibyl
6. **LLM-as-judge** — two-layer (deterministic checks + content quality), replaces heuristic gates
7. **Anti-hallucination** — every citation verified via Semantic Scholar/DBLP
8. **AgentInfra knowledge layer** — .ai/ persists context across stages
9. **Memory Synthesizer** — dedicated skill consolidates .ai/ after each stage (executing skills don't update memory)
10. **Context Chain** — `.ai/context_chain.md` captures reasoning thread across stateless sessions
11. **Fully unattended after Phase 0** — sleep mode with circuit breaker for safety
12. **MCP-first architecture** — prefer MCP tools over Python scripts; scripts remain as fallbacks
13. **Hardware-aware experiments** — hardware_profile.json drives batch sizes, parallelism, framework choices
14. **5-step citation verification** — search → verify in 2+ sources → retrieve BibTeX → validate context → consistent keys
15. **Git pre-registration** — experiment design committed before execution (research(protocol): commits)
16. **Venue-specific checklists** — S8 verifies paper against NeurIPS/ICML/ICLR/ACL requirements

## Changelog

### 2026-03-16 — v2.1 MCP + hardware + research rigor
- Added 3 core MCP servers (Semantic Scholar, System Monitor, SSH) with Python fallbacks
- Added hardware detection (S0_hardware.md → hardware_profile.json)
- All experiment-related skills now hardware-aware (batch size, parallelism, framework)
- Added 5-step citation verification protocol (from Orchestra Research)
- Added venue-specific submission checklists (NeurIPS, ICML, ICLR, ACL, generic)
- Added Git pre-registration protocol for experiments
- Enhanced commit format (research(protocol):, research(results):, research(reflect):)
- Added reference documents (citation-verification.md, agent-continuity.md)

### 2026-03-16 — v2 rewrite
- Replaced Python orchestrator with `run.sh` + .md skills
- Added State Guardian for reliable state progression
- Added Memory Synthesizer + context chain for cross-stage knowledge
- Added cross-model adversarial review (ARIS pattern)
- Added multi-perspective debate (Sibyl pattern)
- Added LLM-as-judge replacing heuristic checks
- Added anti-hallucination citation rules
