# P0 Novelty Check — Verify Research Direction Novelty

> Phase 0, Part 2. Runs after P0_clarification.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: P0`.
2. Read `RESEARCH_PROPOSAL.md` — this is your primary input. If it does not exist, STOP and report error.
3. Read `.ai/core/literature.md` if it exists — prior literature context.
4. Check `state/JUDGE_RESULT.json` — if retrying, read `retry_guidance` and focus on what failed (e.g., "insufficient search breadth", "missed key related work").
5. Check if `RESEARCH_PROPOSAL.md` already has a filled "Novelty Assessment" section:
   - If complete and no retry: skip this skill entirely.
   - If retry: redo the assessment focusing on judge feedback.

## Your Role

You verify that the proposed research direction is sufficiently novel before committing resources. You use a 4-phase verification protocol and produce an honest assessment.

## Process

### Phase 1: Identify Claims

Extract the following from RESEARCH_PROPOSAL.md:
- The core research question (verbatim)
- The proposed method name/description
- The claimed novelty (what is new)
- The target dataset and metric

Formulate 4-6 search queries covering:
1. Exact research question keywords
2. Proposed method name or technique
3. Method + dataset + metric combination
4. Alternative phrasings of the core idea
5. Component techniques (if the method combines known techniques)
6. Application domain + approach type

### Phase 2: Multi-Source Search

For each query, search using:

**Semantic Scholar** (primary):
```bash
python3 scripts/scholarly_search.py --query "<query>" --limit 20
```

**Web search** (supplementary):
Use web search for recent preprints, blog posts, or workshop papers that may not be indexed yet.

Collect all unique results. Target: at least 30 candidate papers across all queries.

### Phase 3: Cross-Verify Similarity

For each candidate paper, classify similarity to the proposal:

| Level | Definition | Criteria |
|-------|-----------|----------|
| **High** | Same question + same approach | Both the research question and method overlap substantially |
| **Medium** | Same question OR same approach | One of the two overlaps, but the other differs |
| **Low** | Tangentially related | Shares a keyword or domain but addresses a different question with a different method |

For high-similarity papers, read the abstract carefully and note:
- What exactly they do that overlaps
- What (if anything) the proposal does differently
- Their results and venue

### Phase 4: Decision and Report

**If >= 3 high-similarity papers found:**

1. Report clearly: "This direction appears well-covered. Found {N} highly similar papers."
2. List each high-similarity paper:
   - Title, authors, year, venue
   - How it overlaps with the proposal
3. Propose **3 adjacent directions** that have gaps:
   - Direction A: {description} — why it is novel
   - Direction B: {description} — why it is novel
   - Direction C: {description} — why it is novel
4. Ask the user to select one or modify the original direction.
5. If the user selects a new direction, update RESEARCH_PROPOSAL.md and re-run phases 1-3 on the new direction.

**If < 3 high-similarity papers found:**

1. Report: "Direction appears novel. Found {N_high} highly similar and {N_med} moderately similar papers."
2. Note any medium-similarity papers that should be cited or compared against.
3. Proceed with the proposed direction.

### Phase 5: Write Outputs

Update `RESEARCH_PROPOSAL.md` "Novelty Assessment" section:

```markdown
## Novelty Assessment

**Status**: {Novel / Partially Novel / Well-Covered}
**High-similarity papers**: {count}
**Search queries used**: {list}

### Most Related Work
1. [{Author}, {Year}] "{Title}" — {venue}. {How it relates and what differentiates our proposal.}
2. ...

### Novelty Justification
{2-3 sentences explaining why this direction is worth pursuing despite existing work.}
```

Create or update `bibliography.bib` with all found papers (high and medium similarity).

## Output

| File | Action |
|------|--------|
| `RESEARCH_PROPOSAL.md` | Update "Novelty Assessment" section |
| `bibliography.bib` | Create/update with found papers in BibTeX format |
| `.ai/core/literature.md` | Update with initial findings from novelty search |

## Anti-Hallucination Protocol

- Every paper you list MUST have been returned by a search query. Do not invent papers.
- If `scholarly_search.py` returns no results for a query, report that honestly.
- If you are uncertain whether a paper exists, search for it explicitly before citing it.
- Include the Semantic Scholar paper ID or DOI when available.

## Rules

- Be honest about overlap. Do not minimize similarity to help the proposal pass.
- If the direction is truly well-covered, say so clearly and help redirect.
- Include both positive and negative evidence in your assessment.
- When proposing adjacent directions, ensure they are actually different — not just rephrased versions.
- If you cannot access Semantic Scholar (API error), fall back to web search and note the limitation.

## When Done

- `RESEARCH_PROPOSAL.md` has a complete "Novelty Assessment" section.
- `bibliography.bib` exists with BibTeX entries for related papers.
- `.ai/core/literature.md` has initial literature context.
- Commit: `P0: novelty assessment complete — {Novel/Partially Novel/Well-Covered}`
- The orchestrator will invoke `judge.md` to evaluate P0 outputs.
