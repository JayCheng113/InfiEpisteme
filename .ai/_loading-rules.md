---
name: Loading Rules
description: Research-specific decision tree for which .ai/ documents to load based on agent role and pipeline stage
---

# Loading Decision Rules — Research Pipeline

## Overview

These rules guide each agent in deciding which .ai/ documents to load. Each agent role has specific document needs.

## Step 1: Always Load

Every agent starts with:
1. `CLAUDE.md` (auto-loaded)
2. `.ai/core/research-context.md` — current research question and hypothesis
3. `.ai/context_chain.md` — reasoning chain across stages (read the last 2-3 entries for recent context)

## Step 2: Load by Agent Role

### Clarification Agent (P0)
- Load nothing extra — starting fresh

### Novelty Check Agent (P0)
- `.ai/core/literature.md` (if exists)

### PhD Agent (S1, S2)
- `.ai/core/literature.md`
- `.ai/core/methodology.md`
- `.ai/evolution/decisions.md`

### Postdoc Agent (S2, S5)
- `.ai/core/methodology.md`
- `.ai/core/literature.md`
- `.ai/evolution/negative-results.md`

### ML Engineer Agent (S3, S4)
- `.ai/core/methodology.md`
- `.ai/evolution/negative-results.md`
- `.ai/evolution/experiment-log.md`

### Experiment Manager Agent (S4)
- `.ai/core/methodology.md`
- `.ai/evolution/experiment-log.md`
- `.ai/evolution/negative-results.md`

### Writing Agent (S6, S7)
- `.ai/core/research-context.md`
- `.ai/core/methodology.md`
- `.ai/core/literature.md`
- `.ai/evolution/decisions.md`

### Reviewer Agent (S7)
- `.ai/core/research-context.md` (only — reviewers should approach the paper fresh)

### Judge Agent (all stages)
- Load only the stage-specific outputs being evaluated

### Memory Synthesizer (runs after every stage)
- ALL `.ai/core/` and `.ai/evolution/` files
- Stage output files (to distill into .ai/)
- `.ai/context_chain.md` (to append new entry)

## Step 3: Budget Check

- Total loaded documents per agent: ≤ 5 (excluding context_chain.md which is always loaded)
- If context is too large, prioritize: research-context > context_chain > methodology > literature
