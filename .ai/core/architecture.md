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
  ├── scripts/parse_state.py → read registry.yaml
  ├── claude -p "skills/_common.md + skills/S{N}.md" → execute stage
  ├── scripts/state_guard.py verify → validate + repair state
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
16 .md files — Claude Code native execution. Each is a complete instruction set:
- `_common.md` — shared preamble (state loading, .ai/ protocol, anti-hallucination)
- `P0_clarification.md`, `P0_novelty.md` — Phase 0 (interactive)
- `S0_init.md` through `S8_delivery.md` — pipeline stages
- `judge.md` — LLM-as-judge (two-layer: deterministic + content quality)
- `vlm_review.md` — VLM figure quality gate

### State Guardian (`scripts/state_guard.py`)
Deterministic Python that validates + repairs state after each skill execution. Ensures pipeline integrity even when Claude Code misses state updates. ~150 lines.

### Python Scripts (`scripts/`)
Minimal CLI tools called by skills via Bash:
- `gpu_submit.py` / `gpu_poll.py` — GPU job management (local + SLURM)
- `cross_review.py` — external model review dispatch (GPT-4o/Gemini)
- `scholarly_search.py` — Semantic Scholar API
- `parse_state.py` / `update_state.py` — YAML read/write

### State Machine (`PIPELINE.md`)
Declarative stage definitions: expected outputs, judge criteria, timeouts, retries. Read by `state_guard.py` for verification.

### State Files
- `registry.yaml` — pipeline position + per-stage status/attempts
- `experiment_tree.json` — experiment tree with node states
- `state/JUDGE_RESULT.json` — latest judge evaluation
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
9. **Fully unattended after Phase 0** — sleep mode with circuit breaker for safety

## Changelog

### 2026-03-16 — v2 rewrite
- Replaced Python orchestrator with `run.sh` + .md skills
- Added State Guardian for reliable state progression
- Added cross-model adversarial review (ARIS pattern)
- Added multi-perspective debate (Sibyl pattern)
- Added LLM-as-judge replacing heuristic checks
- Added anti-hallucination citation rules
