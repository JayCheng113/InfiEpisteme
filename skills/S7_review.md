# S7 Review — Peer Review Simulation

> Stage 7, Part 1. Dispatch and collect reviews.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S7`. Note `review_cycles` count.
2. Read `config.yaml` — cross-review settings (enabled, model, max_rounds).
3. Read `paper.pdf` or `paper/main.tex` + sections — the paper to review.
4. Read `.ai/core/research-context.md` — research question context.
5. Check `state/REVIEW_STATE.json` — if it exists:
   - Read current cycle number.
   - Read scores from previous cycles.
   - If max cycles (4) reached: report completion, do not start a new cycle.
6. Check `state/JUDGE_RESULT.json` — if retrying, read `retry_guidance`.

### Review References
- **Reviewer evaluation criteria and scoring**: Read `skills/references/reviewer-guidelines.md`

### Idempotency Check
- Check `reviews/cycle_{N}/` for the current cycle.
- If all 3 reviews exist for this cycle: skip to aggregation.
- If partial: generate only the missing reviews.

### Safety Check
- Read `review_cycles` from registry.yaml or state/REVIEW_STATE.json.
- If `review_cycles >= config.cross_review.max_rounds` (default 4): STOP. Max cycles reached.

## Your Role

You orchestrate peer review with 3 distinct reviewer personas. Two are dispatched externally (via cross_review.py), and one is performed internally.

## Process

### Step 1: Determine Current Cycle

```python
cycle_num = state.get("review_cycles", 0) + 1
if cycle_num > config["cross_review"]["max_rounds"]:
    # Max cycles reached — report final scores and stop
    stop()
```

Create directory: `reviews/cycle_{cycle_num}/`

### Step 2: Dispatch External Reviews (R1 and R3)

If `config.cross_review.enabled` is true:

```bash
python3 scripts/cross_review.py \
  --paper paper/main.tex \
  --persona R1 \
  --output reviews/cycle_{cycle_num}/R1_review.md

python3 scripts/cross_review.py \
  --paper paper/main.tex \
  --persona R3 \
  --output reviews/cycle_{cycle_num}/R3_review.md
```

**R1: Methods-Focused Reviewer**
- Focus: technical soundness, experimental rigor
- Skeptical of claims not backed by ablations
- Wants: statistical significance, error bars, ablation studies
- Common critiques: "missing ablation for X", "no significance test", "claim Y is unsupported"

**R3: Novelty-Focused Reviewer**
- Focus: contribution significance, comparison to prior work
- Compares carefully against related work
- Wants: clear differentiation, meaningful improvement
- Common critiques: "incremental over [paper]", "missing comparison to [method]"

If `cross_review.py` fails:
- Log the error.
- Fall back to internal review for R1 and R3 as well.
- Note the limitation in the review cycle summary.

### Step 3: Internal Review (R2)

You perform R2 yourself as a clarity-focused reviewer.

**R2: Clarity-Focused Reviewer**
- Focus: writing quality, organization, accessibility
- Wants: clear motivation, good examples, intuitive explanations
- Read the paper as if encountering it for the first time

Produce the review in this exact format:

```markdown
## Reviewer R2 — Clarity and Presentation

### Scores
- Soundness: {1-4}
- Presentation: {1-4}
- Contribution: {1-4}
- Overall: {1-10}

### Summary
{2-3 sentences summarizing the paper}

### Strengths
1. {strength — be specific}
2. {strength}
3. {strength}

### Weaknesses
1. {weakness — be specific and actionable, with suggested fix}
2. {weakness}
3. {weakness}

### Questions for Authors
1. {question}

### Suggestions
1. {suggestion}

### Decision
{Accept / Weak Accept / Borderline / Weak Reject / Reject}
```

Save to `reviews/cycle_{cycle_num}/R2_review.md`.

### Step 4: Aggregate Reviews

Read all 3 reviews and compute:

```json
{
  "cycle": N,
  "reviews": {
    "R1": { "soundness": X, "presentation": X, "contribution": X, "overall": X, "decision": "..." },
    "R2": { "soundness": X, "presentation": X, "contribution": X, "overall": X, "decision": "..." },
    "R3": { "soundness": X, "presentation": X, "contribution": X, "overall": X, "decision": "..." }
  },
  "average_overall": X.X,
  "average_soundness": X.X,
  "average_presentation": X.X,
  "average_contribution": X.X,
  "consensus_decision": "...",
  "critical_weaknesses": ["...", "..."],
  "minor_weaknesses": ["...", "..."]
}
```

Classify each weakness:
- **Critical**: affects soundness or requires new experiments
- **Minor**: affects clarity or requires textual changes
- **Question**: requires clarification but not changes

Save to `reviews/cycle_{cycle_num}/aggregate.json`.

### Step 5: Write Cycle Summary

Create `reviews/cycle_{cycle_num}/summary.md`:

```markdown
# Review Cycle {N} Summary

## Scores
| Reviewer | Soundness | Presentation | Contribution | Overall |
|----------|-----------|-------------|-------------|---------|
| R1       | ...       | ...         | ...         | ...     |
| R2       | ...       | ...         | ...         | ...     |
| R3       | ...       | ...         | ...         | ...     |
| **Avg**  | ...       | ...         | ...         | ...     |

## Consensus: {decision}

## Critical Weaknesses (must address)
1. {weakness + which reviewer raised it}

## Minor Weaknesses (should address)
1. {weakness}

## Action Required
{If average_overall >= target_score: "PASS — paper meets quality threshold."}
{If average_overall < target_score: "REVISE — invoke S7_revise to address weaknesses."}
```

### Step 6: Update State

Update `state/REVIEW_STATE.json`:
```json
{
  "current_cycle": N,
  "cycles": [
    {
      "cycle": N,
      "average_score": X.X,
      "decision": "...",
      "timestamp": "..."
    }
  ],
  "passed": true/false,
  "pass_reason": "score >= target" | "max_cycles_reached" | null
}
```

Update `registry.yaml`:
- `review_cycles: N`
- `current_score: X.X`

## Output

| File | Action |
|------|--------|
| `reviews/cycle_{N}/R1_review.md` | External review |
| `reviews/cycle_{N}/R2_review.md` | Internal review |
| `reviews/cycle_{N}/R3_review.md` | External review |
| `reviews/cycle_{N}/aggregate.json` | Aggregated scores and weaknesses |
| `reviews/cycle_{N}/summary.md` | Cycle summary |
| `state/REVIEW_STATE.json` | Update review state |
| `registry.yaml` | Update review_cycles and current_score |

## Quality Rules

- Each reviewer persona reviews independently — do not reference other reviews during generation.
- Be constructive — every weakness must suggest how to fix it.
- Be specific — "writing is unclear" is useless; "Section 3.2 conflates X and Y" is actionable.
- Score honestly — do not inflate scores. NeurIPS calibration:
  - 1-3: Clear reject
  - 4-5: Weak reject / Borderline
  - 6-7: Weak accept / Accept (good paper)
  - 8-10: Strong accept (excellent paper, top 5-15%)
- A good paper at a top venue should score 6-7.

## Anti-Gaming Rule (from ARIS)

- Reviewers must NOT hide weaknesses to inflate scores.
- If the paper has real problems, they must be identified.
- The goal is to improve the paper, not to pass the gate.

## When Done

- All reviews for cycle N are written.
- Aggregate scores computed.
- State files updated.
- If `average_overall >= target_score`: report PASS.
- If `average_overall < target_score` and `cycle < max_rounds`: invoke S7_revise next.
- If `cycle >= max_rounds`: report completion regardless of score.
- Commit: `S7: review cycle {N} — avg score {X.X}`
