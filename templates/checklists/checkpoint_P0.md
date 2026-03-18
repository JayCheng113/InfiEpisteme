# Human Checkpoint: P0 — Research Direction

> Fixed checklist. These items come from real failure modes observed in production runs.
> Answer each item before approving the research direction.

## Layer A: Fixed Checklist (human-designed)

- [ ] **Hypothesis framing**: Read the hypothesis in RESEARCH_PROPOSAL.md. Is it a testable question, or a disguised assertion? (e.g., "X will underperform Y because Z" is an assertion without evidence — reframe as "How does X compare to Y on Z?")
- [ ] **Factual claims**: Spot-check 1-2 claims about prior work against the actual papers. Does the proposal accurately describe what prior work tested and on what scale?
- [ ] **Scope for venue**: Is the experimental scope (number of architectures, scales, baselines) sufficient for the target venue? A single architecture at a single scale is rarely enough for a top venue.
- [ ] **Compute feasibility**: Rough check — number of experiments × estimated hours per experiment. Does it fit the GPU budget with room for retries and ablations?
- [ ] **Novelty**: Is the claimed research gap real? Has someone already done this comparison or proposed this method?

## Layer B: LLM Adversarial Brief

> Auto-generated below by the judge. These are the things the LLM is least confident about.

{LLM_BRIEF}

## Layer C: Raw Files

Review these files if any checklist item raises concerns:
- `RESEARCH_PROPOSAL.md` — full proposal
- `bibliography.bib` — cited papers (if exists at this stage)
- `.ai/core/research-context.md` — research context

## Response

Approve: `./run.sh approve`
Approve with changes: `./run.sh approve --with "your modifications here"`
