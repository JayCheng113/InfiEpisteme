# Checkpoint — Human Review Gate

> Generates a checkpoint document for human review at critical decision points.
> Triggered after judge passes for P0 and S2.

## When This Runs

This skill runs after the judge passes for P0 or S2. It does NOT replace the judge — it adds a human review layer on top of the automated review.

## Input

- `registry.yaml` — current stage (P0 or S2)
- `state/JUDGE_RESULT.json` — judge's evaluation (already passed)
- Stage outputs (RESEARCH_PROPOSAL.md for P0, EXPERIMENT_PLAN.md + experiment_tree.json for S2)
- Fixed checklist template from `templates/checklists/checkpoint_{stage}.md`

## Process

### Step 1: Read the Fixed Checklist Template

Read `templates/checklists/checkpoint_{stage}.md` where `{stage}` is P0 or S2.

### Step 2: Generate Adversarial Brief

Write a short (5-10 line) adversarial brief covering:

1. **Top 3 things I am least confident about** — specific claims, design choices, or assumptions where you have genuine uncertainty. Be honest — if you relied on LLM knowledge rather than verified sources, say so.
2. **What could go wrong** — the single biggest risk if we proceed as planned.
3. **What I would change** — if you had to improve one thing about this stage's output, what would it be?

Rules for the brief:
- Be genuinely adversarial, not performatively cautious.
- Cite specific content from the stage outputs (quote the claim, name the node).
- Do NOT pad with generic concerns ("there might be issues with..."). Be specific or say nothing.

### Step 3: Assemble Checkpoint Document

1. Read the fixed checklist template.
2. Replace `{LLM_BRIEF}` with the adversarial brief from Step 2.
3. Write to `state/CHECKPOINT_{stage}.md`.

Note: Do NOT modify registry.yaml. The orchestrator (run.sh) handles state transitions.

## Output

| File | Action |
|------|--------|
| `state/CHECKPOINT_{stage}.md` | Assembled checkpoint document |
| `registry.yaml` | Status set to `awaiting_human` |

## When Done

- Print: "CHECKPOINT: Human review required. See state/CHECKPOINT_{stage}.md"
- Pipeline pauses until human responds.
