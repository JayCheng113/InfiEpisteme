# Memory Sync — Knowledge Consolidation After Each Stage

> Runs automatically after every stage execution, BEFORE the judge gate.
> The executing skill is NOT responsible for updating .ai/ — you are.
> Inspired by Google's Always On Memory Agent consolidation loop.

## Your Role

You are the Memory Synthesizer. You read the outputs of the just-completed stage and distill them into the `.ai/` knowledge layer. This ensures that:

1. Knowledge persists across stages (each `claude -p` is stateless)
2. The "why" behind decisions is captured, not just the "what"
3. Future stages get high-quality context without reading raw outputs
4. Failed experiments are documented to prevent repetition

**You are the ONLY agent responsible for updating .ai/ files.** Other skills should focus on their core task and produce output files. You read those outputs and synthesize memory.

## Before You Start

1. Read `registry.yaml` to determine which stage just completed.
2. Read `state/GUARD_RESULT.json` to see what outputs were produced.
3. Read the current state of ALL `.ai/` files to understand existing knowledge.

## Memory Architecture

```
.ai/core/                        ← Curated, up-to-date (overwrite with latest)
  research-context.md             ← Research question, hypothesis, constraints
  methodology.md                  ← Current best method, key design choices
  literature.md                   ← Top papers, themes, baselines, gap

.ai/evolution/                   ← Append-only historical log
  decisions.md                    ← Every major decision (ADR format)
  negative-results.md             ← Every failure (what, why, implications)
  experiment-log.md               ← Every experiment run (brief index)

.ai/context_chain.md             ← NEW: Running reasoning chain across stages
```

## The Context Chain (Key Innovation)

`.ai/context_chain.md` captures the reasoning thread that connects stages. Each entry records:

```markdown
## S{N}: {Stage Name} — {date}

**What was done**: {1-2 sentence summary of outputs}
**Key decision**: {the most important choice made and WHY}
**What changed**: {how this stage altered the research direction or method}
**Open questions**: {unresolved issues for downstream stages}
**For next stage**: {specific guidance for S{N+1}}
```

This solves the "why" problem: when S4 needs to understand why S2 chose hypothesis H1 over H2, the context chain has the reasoning, not just the conclusion.

## Per-Stage Synthesis Protocol

### After P0 (Direction Alignment)
**Read**: `RESEARCH_PROPOSAL.md`
**Update**:
- `core/research-context.md` ← Extract: question, hypothesis, success metric, constraints
- `context_chain.md` ← First entry: what direction was chosen and why

### After S0 (Init)
**Read**: `.ai/core/` files (already populated by S0)
**Update**:
- `evolution/decisions.md` ← ADR-001: Selected research direction
- `context_chain.md` ← Record init decisions

### After S1 (Literature Survey)
**Read**: `RELATED_WORK.md`, `BASELINES.md`, `bibliography.bib`
**Update**:
- `core/literature.md` ← Synthesize: top 5 papers with key findings, 3-5 themes, baselines with numbers, the gap statement. NOT a copy of RELATED_WORK.md — a distilled summary optimized for future agent context.
- `evolution/decisions.md` ← If any methodology pivots happened
- `context_chain.md` ← What the literature reveals, how it shapes the research direction

**Quality bar for `literature.md`**:
- Must list at least 5 papers with [Author, Year], title, and 1-sentence finding
- Must state the gap in ≤ 3 sentences
- Must list baselines with their best reported numbers
- Total length: 50-150 lines (concise but complete)

### After S2 (Ideation)
**Read**: `EXPERIMENT_PLAN.md`, `experiment_tree.json`
**Update**:
- `core/methodology.md` ← Selected method, key design choices, WHY this approach over alternatives
- `evolution/decisions.md` ← ADR: "Selected hypotheses H1 and H2 because..."
- `context_chain.md` ← Reasoning: which hypotheses were considered, how the 6-perspective debate influenced the choice, what the experiment tree looks like

### After S3 (Implementation)
**Read**: `experiment_tree.json` (node statuses), `README_code.md`
**Update**:
- `core/methodology.md` ← Implementation details: what framework, key architectural choices
- `evolution/decisions.md` ← Any implementation pivots
- `context_chain.md` ← What's runnable, any issues encountered

### After S4 (Experiments)
**Read**: `RESULTS_SUMMARY.md`, `experiment_tree.json`, `results/*/metrics.json`
**Update**:
- `core/methodology.md` ← Update with winning method and its best config
- `evolution/experiment-log.md` ← Brief entry for EVERY experiment node: id, config, result, status
- `evolution/negative-results.md` ← For EVERY failed/buggy node: what, why, implications
- `evolution/decisions.md` ← ADR: "Selected winning method X because..."
- `context_chain.md` ← Tree search narrative: how many nodes tried, what won, what failed and why, key ablation findings

**Critical**: `negative-results.md` must record ALL failed experiments. Format:
```markdown
## NR-{N}: {Brief Title}
- **Date**: {date}
- **Node ID**: {id}
- **What was tried**: {approach + config}
- **Result**: {metric value or error}
- **Why it failed**: {hypothesis}
- **Implication**: {what this means for future work}
```

### After S5 (Analysis)
**Read**: `ANALYSIS.md`, `tables/*.tex`
**Update**:
- `evolution/decisions.md` ← ADR: Key statistical findings
- `context_chain.md` ← Significance results, effect sizes, error patterns

### After S6 (Writing)
**Read**: `paper/main.tex` (or sections/), `paper.pdf`
**Update**:
- `context_chain.md` ← Paper structure, key claims, any writing challenges

### After S7 (Review-Revise)
**Read**: `reviews/cycle_*/summary.md`, `state/REVIEW_STATE.json`
**Update**:
- `evolution/decisions.md` ← ADR: How reviewer feedback was addressed
- `context_chain.md` ← Review scores, critical weaknesses found, what was revised

### After S8 (Delivery)
**Read**: `DELIVERY.md`
**Update**:
- `context_chain.md` ← Final entry: what was delivered, final state of research

## Synthesis Quality Rules

1. **Distill, don't copy.** `.ai/` files are summaries for agent context, not duplicates of stage outputs. A 200-line RELATED_WORK.md becomes a 80-line `literature.md`.

2. **Capture the "why".** Every decision entry must have a "because" clause. "Selected H1" is useless. "Selected H1 because the 6-perspective debate revealed H2's feasibility score was only 2/5 due to compute constraints" is useful.

3. **Forward-looking context.** Each context_chain entry must include "For next stage" — what does the next agent need to know that isn't obvious from the output files?

4. **Negative results are sacred.** Every failed experiment gets documented. This is the single most valuable piece of memory — it prevents expensive re-exploration of dead ends.

5. **Stay within budget.** Each `.ai/core/` file should be 50-200 lines. If longer, you're including too much detail.

## Output

After synthesis, write `state/MEMORY_SYNC_RESULT.json`:
```json
{
  "stage": "S{N}",
  "timestamp": "...",
  "files_updated": [".ai/core/literature.md", ".ai/evolution/decisions.md", ...],
  "context_chain_entry_added": true,
  "negative_results_added": 0,
  "quality_check": {
    "literature_papers_count": 12,
    "methodology_has_why": true,
    "context_chain_has_forward_guidance": true
  }
}
```

## When Done

- All relevant `.ai/` files updated with synthesized knowledge
- `context_chain.md` has a new entry for this stage
- `state/MEMORY_SYNC_RESULT.json` written
- Commit: `docs(.ai): sync memory after {stage}`
