# S0 Init — Bootstrap Knowledge Base

> Stage 0. Runs once after P0 completes.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S0`.
2. Read `RESEARCH_PROPOSAL.md` — this is your primary input. If it does not exist or is missing required fields, STOP and report error.
3. Read `config.yaml` — get target venue and compute settings.
4. Check `state/JUDGE_RESULT.json` — if retrying, read `retry_guidance`.
5. Check if `.ai/core/research-context.md` already has substantive content:
   - If all .ai/ files are already populated: verify completeness and skip if valid.

## Your Role

You bootstrap the `.ai/` knowledge base from RESEARCH_PROPOSAL.md so that all subsequent skills have a shared context foundation. You also create the first Architecture Decision Record (ADR).

## Process

### Step 1: Ensure Directory Structure

Verify these directories exist; create any that are missing:

```
.ai/
  core/
    architecture.md
    research-context.md
    methodology.md
    literature.md
  evolution/
    decisions.md
    negative-results.md
    experiment-log.md
state/
results/
paper/
  sections/
  figures/
tables/
figures/
  analysis/
reviews/
DELIVERY/
```

### Step 2: Populate `.ai/core/research-context.md`

Read RESEARCH_PROPOSAL.md and write:

```markdown
# Research Context

## Research Question
{from RESEARCH_PROPOSAL.md}

## Hypothesis
{from RESEARCH_PROPOSAL.md}

## Success Criteria
- Primary metric: {from success_metric}
- Target: {from success_metric}

## Constraints
- Compute: {gpu_hours} GPU-hours on {gpu_type}
- Deadline: {deadline}
- Target venue: {from config.yaml}

## Novelty Assessment Summary
{from RESEARCH_PROPOSAL.md novelty assessment section}

## Current Status
Stage S0 complete. Proceeding to literature survey.
```

### Step 3: Populate `.ai/core/methodology.md`

```markdown
# Methodology

## Proposed Approach
{from RESEARCH_PROPOSAL.md proposed_method}

## Baselines
{from RESEARCH_PROPOSAL.md baselines list}

## Key Design Decisions
(To be populated during S2 ideation)

## Implementation Status
Not started. Pending S3.
```

### Step 4: Populate `.ai/core/literature.md`

```markdown
# Literature Context

## Initial Papers
{from bibliography.bib if it exists — list paper titles and relevance}
{if bibliography.bib does not exist: "No papers found yet. Will be populated during S1."}

## Key Themes
(To be populated during S1 literature survey)

## Known Baselines
{from RESEARCH_PROPOSAL.md baselines}
```

### Step 5: Create ADR-001

Append to `.ai/evolution/decisions.md`:

```markdown
## ADR-001: Research Direction Selection

**Date**: {today}
**Status**: Accepted
**Context**: User completed Phase 0 alignment, selecting a research direction.
**Decision**: Pursue "{research_question}" with approach "{proposed_method}".
**Rationale**: Novelty assessment indicates {Novel/Partially Novel}. Feasible within {gpu_hours} GPU-hours budget.
**Consequences**: Pipeline proceeds to S1 literature survey. Direction locked unless S1 reveals fundamental issues.
```

### Step 6: Initialize Empty Evolution Logs

If not already present, ensure these files have headers:

`.ai/evolution/negative-results.md`:
```markdown
# Negative Results Log

> Every failed experiment must be recorded here to prevent repeating mistakes.
```

`.ai/evolution/experiment-log.md`:
```markdown
# Experiment Log

> Brief record of every experiment run.

| Date | Node ID | Description | Result | Notes |
|------|---------|-------------|--------|-------|
```

### Step 7: Verify `.ai/core/architecture.md`

If this file is empty or missing, populate it with the pipeline architecture:

```markdown
# System Architecture

## Pipeline
P0 (Direction Alignment) -> S0 (Init) -> S1 (Literature) -> S2 (Ideation) -> S3 (Code) -> S4 (Experiments) -> S5 (Analysis) -> S6 (Writing) -> S7 (Review-Revise) -> S8 (Delivery)

## Key Files
- `config.yaml` — user configuration
- `registry.yaml` — pipeline state machine
- `experiment_tree.json` — experiment tree structure
- `PIPELINE.md` — stage definitions and criteria

## Directory Layout
- `src/` — implementation code
- `results/` — experiment outputs per node
- `paper/` — LaTeX paper
- `state/` — judge results and review state
- `.ai/` — knowledge base for agent context
```

## Output

| File | Action |
|------|--------|
| `.ai/core/research-context.md` | Create/update |
| `.ai/core/methodology.md` | Create/update |
| `.ai/core/literature.md` | Create/update |
| `.ai/core/architecture.md` | Create/update if missing |
| `.ai/evolution/decisions.md` | Append ADR-001 |
| `.ai/evolution/negative-results.md` | Ensure header exists |
| `.ai/evolution/experiment-log.md` | Ensure header exists |
| Directories | Create any missing directories |

## Rules

- Do not modify RESEARCH_PROPOSAL.md — it is locked after P0.
- Do not perform any literature search — that is S1's job.
- Do not generate hypotheses — that is S2's job.
- Keep all content factual and sourced from RESEARCH_PROPOSAL.md.
- If bibliography.bib exists, extract paper info; do not invent entries.

## When Done

- All `.ai/core/` files have substantive content derived from RESEARCH_PROPOSAL.md.
- ADR-001 exists in `.ai/evolution/decisions.md`.
- All required directories exist.
- Commit: `S0: bootstrap knowledge base from research proposal`
- Commit: `docs(.ai): initialize core context and ADR-001`
