# InfiEpisteme Pipeline Definition

> This file defines the state machine for the automated research pipeline.
> `run.sh` reads this to orchestrate stage execution.
> `scripts/state_guard.py` reads this to verify stage outputs.

## Stage Order

[Hardware Detection] → P0 → S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → COMPLETE

### Hardware Detection (Pre-Stage)
**Skill**: `S0_hardware.md`
**Trigger**: Runs automatically at pipeline start if `hardware_profile.json` does not exist.
**Timeout**: 2m
**Output**: `hardware_profile.json`
**Not a formal stage** — no judge gate, no retry logic. Failure is non-fatal (skills proceed without hardware constraints).

## Stage Definitions

### P0 — Direction Alignment
**Skills**: `P0_clarification.md`, `P0_novelty.md`
**Mode**: Interactive (user present)
**Timeout**: 30m
**Max Retries**: 1

```yaml
expected_outputs:
  - RESEARCH_PROPOSAL.md
expected_ai_updates:
  - .ai/core/research-context.md
registry_fields: {}
```

**Judge criteria**: RESEARCH_PROPOSAL.md exists with all required fields (research_question, hypothesis, proposed_method, baselines, success_metric)

---

### S0 — Init
**Skill**: `S0_init.md`
**Timeout**: 5m
**Max Retries**: 2

```yaml
expected_outputs: []
expected_ai_updates:
  - .ai/core/research-context.md
  - .ai/core/methodology.md
  - .ai/evolution/decisions.md
registry_fields: {}
```

**Judge criteria**: .ai/core/ files populated with content from RESEARCH_PROPOSAL.md; `hardware_profile.json` exists with valid hardware data

---

### S1 — Literature Survey
**Skill**: `S1_literature.md`
**Timeout**: 20m
**Max Retries**: 3

```yaml
expected_outputs:
  - RELATED_WORK.md
  - BASELINES.md
  - bibliography.bib
expected_ai_updates:
  - .ai/core/literature.md
registry_fields:
  papers_reviewed: ">= 20"
  baselines_identified: ">= 3"
```

**Judge criteria**:
- ≥20 papers reviewed with proper citations
- ≥3 baselines identified with reported numbers
- Research gap clearly stated connecting to research question
- All citations traceable to real papers (anti-hallucination)

---

### S2 — Ideation + Experimental Design
**Skill**: `S2_ideation.md`
**Timeout**: 15m
**Max Retries**: 3

```yaml
expected_outputs:
  - EXPERIMENT_PLAN.md
  - experiment_tree.json
expected_ai_updates:
  - .ai/core/methodology.md
  - .ai/evolution/decisions.md
registry_fields:
  hypotheses_selected: ">= 2"
  root_nodes: ">= 6"
```

**Judge criteria**:
- ≥2 hypotheses selected with feasibility/novelty/impact scores
- Experiment tree has ≥6 root nodes (N=3 per hypothesis)
- Each node has clear success metric and approach description
- Multi-perspective critique completed (6 viewpoints)

---

### S3 — Code Implementation
**Skill**: `S3_implementation.md`
**Timeout**: 30m
**Max Retries**: 3

```yaml
expected_outputs:
  - src/method/
  - src/baselines/
  - src/evaluation/
  - requirements.txt
  - README_code.md
expected_ai_updates:
  - .ai/evolution/experiment-log.md
registry_fields: {}
```

**Judge criteria**:
- All root nodes in experiment_tree.json have status=runnable
- Baselines implemented and verified against reported numbers (±5%)
- Evaluation harness runs without errors on test data
- README_code.md has reproduction instructions

---

### S4 — Experiment Tree Search
**Skill**: `S4_experiments.md` (orchestrates `S4_run_node.md`)
**Timeout**: 120m
**Max Retries**: 3

```yaml
expected_outputs:
  - RESULTS_SUMMARY.md
expected_ai_updates:
  - .ai/evolution/experiment-log.md
  - .ai/evolution/negative-results.md
registry_fields:
  tree_stages_complete: "4"
```

**Judge criteria**:
- Stage 4.4 (ablation studies) complete
- ≥1 method outperforms all baselines on primary metric
- All figures VLM-approved (score ≥ 4/5)
- Negative results documented in .ai/evolution/negative-results.md

**Safety**: Experiments >4 GPU-hours require explicit budget check. Circuit breaker on consecutive failures.

---

### S5 — Analysis + Significance Testing
**Skill**: `S5_analysis.md`
**Timeout**: 15m
**Max Retries**: 3

```yaml
expected_outputs:
  - ANALYSIS.md
  - tables/
  - figures/analysis/
expected_ai_updates:
  - .ai/evolution/decisions.md
registry_fields: {}
```

**Judge criteria**:
- Statistical significance tests run on all main comparisons
- P-values computed and reported with effect sizes
- Error analysis with categorized failure modes
- Multi-perspective analysis completed (6 result-analysis viewpoints)
- All analysis figures VLM-approved

---

### S6 — Paper Writing
**Skill**: `S6_writing.md`
**Timeout**: 25m
**Max Retries**: 3

```yaml
expected_outputs:
  - paper/main.tex
  - paper/sections/
  - paper.pdf
expected_ai_updates: []
registry_fields: {}
```

**Judge criteria**:
- LaTeX compiles without errors (pdflatex exit code 0)
- PDF renders correctly (page count > 0)
- All figures referenced in text are present in paper/figures/
- All citations in text have corresponding bibliography entries
- No hallucinated citations (every \cite{} matches a real bibliography.bib entry)

---

### S7 — Review-Revise Cycle
**Skills**: `S7_review.md`, `S7_revise.md`
**Timeout**: 30m per cycle
**Max Retries**: 3
**Max Review Cycles**: 4 (from ARIS safety limit)

```yaml
expected_outputs:
  - reviews/
expected_ai_updates: []
registry_fields:
  review_cycles: ">= 1"
  current_score: ">= 0"
```

**Judge criteria (pass if EITHER)**:
- Average reviewer score ≥ target_score (default 6.0/10)
- OR: max review cycles (4) completed

**Cross-model review**: R1 (methods) + R3 (novelty) use external model. R2 (clarity) uses Claude.

---

### S8 — Delivery
**Skill**: `S8_delivery.md`
**Timeout**: 15m
**Max Retries**: 2

```yaml
expected_outputs:
  - DELIVERY/paper.pdf
  - DELIVERY/code/
  - DELIVERY/results/
  - DELIVERY/README.md
  - DELIVERY.md
  - DELIVERY/checklist_report.md
expected_ai_updates: []
registry_fields: {}
```

**Judge criteria**:
- paper.pdf renders correctly
- Code runs from DELIVERY/README.md instructions
- Results in DELIVERY/results/ match numbers in paper
- DELIVERY.md summary present
- DELIVERY/checklist_report.md exists with venue-specific verification

---

## Error Recovery

| Error Type | Detection | Recovery |
|---|---|---|
| Skill timeout | run.sh timeout | Re-invoke skill (idempotent) |
| Judge failure | JUDGE_RESULT.json | Re-invoke with retry_guidance |
| GPU crash | gpu_poll.py exit code | Resume from checkpoint or re-submit |
| API rate limit | scripts exit code | Exponential backoff in Python |
| MCP unavailable | tool call error | Fallback to Python scripts (see _common.md) |
| Cross-review fail | cross_review.py exit | Fall back to internal review |
| LaTeX compile fail | pdflatex exit code | Skill fixes .tex and retries |
| Context overflow | Claude Code error | State persisted; resume from registry |

## Circuit Breaker

If the same criterion fails 3 consecutive times across retries:
1. `state_guard.py` detects via `consecutive_same_failure` counter
2. Pipeline pauses with explicit error message
3. User must intervene and `./run.sh resume` after fixing

## Safety Limits (from ARIS)

- Max review cycles: 4 (prevents infinite review loops)
- Max GPU hours per experiment: skip if >4h without explicit budget
- Anti-hallucination: every citation must be verifiable via Semantic Scholar/DBLP (5-step verification protocol)
- Anti-gaming: reviewers must not hide weaknesses to inflate scores
- Git pre-registration: experiment design committed before running (research(protocol): commits)
