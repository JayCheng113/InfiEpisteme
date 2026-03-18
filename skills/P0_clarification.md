# P0 Clarification — Direction Alignment

> Phase 0, Part 1. Runs on the server via `claude -p` (non-interactive).
> The local CC has already discussed the research direction with the user and written `config.yaml`.
> This skill formalizes `config.yaml` into a structured `RESEARCH_PROPOSAL.md`.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: P0`.
2. Read `config.yaml` — the `research_direction` field contains the user's research intent (written by local CC after user discussion).
3. Read `hardware_profile.json` if it exists — hardware capabilities affect scope decisions. If missing, proceed without hardware-aware scope validation (note that scope estimates may be less precise).
4. Check if `RESEARCH_PROPOSAL.md` already exists:
   - If it exists and has all required fields filled: verify completeness and skip.
   - If it exists but is incomplete: resume from the first missing field.
5. Read `.ai/core/research-context.md` if it exists — there may be prior context from a previous attempt.
6. Check `state/JUDGE_RESULT.json` — if this is a retry, read `retry_guidance` and focus on the flagged gaps.

## Your Role

You are the Direction Alignment skill. Your job is to formalize the research direction from `config.yaml` into a structured, complete `RESEARCH_PROPOSAL.md`. You do NOT ask questions — the user has already been consulted by local CC.

## Process

### Step 1: Extract and Expand

Read `config.yaml` fields:
- `research_direction` — the core research intent
- `target_venue` — venue constraints (page limits, review criteria)
- `compute.gpu_hours`, `compute.gpu_type` — resource constraints

From `research_direction`, identify and extract:
1. **Research question** — one precise sentence
2. **Testable hypothesis** — a falsifiable claim (phrase as question if speculative)
3. **High-level methodology** — 2-3 sentences on the approach
4. **Likely baselines** — what to compare against
5. **Success metric** — exact measurement (e.g., "perplexity improvement, p < 0.05")
6. **Compute budget** — from config fields

If `research_direction` is too vague to extract all 6 elements (e.g., just "I want to study attention"), write what you can extract to `RESEARCH_PROPOSAL.md` with `[NEEDS CLARIFICATION]` markers on missing fields, and note in the commit message that the proposal is incomplete. The judge will flag this and the user will be asked to provide more detail.

### Step 2: Validate Scope

Check that the proposed scope is feasible:
- Does the compute budget support the proposed experiments? (rough estimate)
- Is the scope appropriate for the target venue?
- Are the baselines reasonable and available?

If scope issues are found, note them in the proposal under a "## Scope Concerns" section rather than silently adjusting. The human checkpoint after P0 will catch these.

### Step 3: Write Output

Write `RESEARCH_PROPOSAL.md` using the template structure from `templates/RESEARCH_PROPOSAL.md`:

```markdown
# Research Proposal

## Research Question
{one sentence}

## Hypothesis
{testable claim}

## Proposed Method
{high-level approach — 2-3 sentences}

## Baselines
- {baseline 1}: {brief description}
- {baseline 2}: {brief description}

## Success Metric
{exact measurement}

## Compute Budget
- GPU hours: {N}
- GPU type: {type}
- Parallel jobs: {N}

## Deadline
{target submission date or "no deadline"}

## Novelty Assessment
{to be filled by P0_novelty skill}
```

## Output

| File | Action |
|------|--------|
| `RESEARCH_PROPOSAL.md` | Create or update |
| `.ai/core/research-context.md` | (updated by memory_sync — do not write directly) |

## Rules

- Do NOT ask questions or wait for user input. You are running non-interactively via `claude -p`.
- The user has already been consulted by local CC. Your input is `config.yaml`.
- If `research_direction` is insufficient, write what you can and mark gaps with `[NEEDS CLARIFICATION]`.
- Do not run novelty checks — that is the next skill's job (P0_novelty).
- Do not invent a research direction. Only formalize what `config.yaml` provides.

## When Done

- `RESEARCH_PROPOSAL.md` exists with all fields except "Novelty Assessment" filled (or marked `[NEEDS CLARIFICATION]`).
- Commit: `P0: research proposal formalized from config.yaml`
