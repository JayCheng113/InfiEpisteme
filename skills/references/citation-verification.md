# Citation Verification Protocol — 5-Step Process

> Reference document for all skills that produce or verify citations.
> Adapted from Orchestra Research `20-ml-paper-writing/references/citation-verification.md`.

## Overview

Every citation in InfiEpisteme outputs must be **real, verifiable, and correctly attributed**. LLM-generated citations have a ~40% error rate. This protocol eliminates hallucinated references.

## The 5 Steps

### Step 1: Search

Find candidate papers using Semantic Scholar MCP or fallback:

**Primary (MCP)**:
- Use `mcp__semantic-scholar__search_papers` with the paper title or key terms.

**Fallback (Python script)**:
- `python3 scripts/scholarly_search.py search "<title or keywords>"`

**Supplementary**:
- Web search with `site:arxiv.org` or `site:scholar.google.com` for very recent papers.

Search for the **exact title** first. If no exact match, search for key terms from the title.

### Step 2: Verify (2+ Independent Sources)

Confirm the paper exists in at least 2 independent sources:

| Source 1 | Source 2 (pick one) |
|----------|-------------------|
| Semantic Scholar | arXiv |
| Semantic Scholar | CrossRef (via DOI) |
| Semantic Scholar | Google Scholar (web search) |
| Semantic Scholar | DBLP |

Check that these fields match across sources:
- Title (exact or near-exact)
- First author last name
- Year (exact)
- Venue (if published — preprints may only be on arXiv)

**If a paper cannot be confirmed in 2 sources: DO NOT CITE IT.**

### Step 3: Retrieve BibTeX

Get BibTeX from an authoritative source — **never generate BibTeX from LLM memory**.

**Preferred sources** (in order):
1. Semantic Scholar MCP: `mcp__semantic-scholar__get_paper_details` → extract citation info
2. Semantic Scholar API via script: `python3 scripts/scholarly_search.py bibtex <PAPER_ID>`
3. arXiv: `https://arxiv.org/abs/<id>` → "Export BibTeX" link
4. DBLP: `https://dblp.org/` → BibTeX export
5. CrossRef: DOI-based BibTeX retrieval

**Never**:
- Write BibTeX fields from memory
- Guess the venue, year, or page numbers
- Copy BibTeX from a different paper with similar name

### Step 4: Validate Citation Context

For each citation, verify that:
1. The paper's actual content supports your citation claim.
2. Read the abstract (at minimum) to confirm relevance.
3. If you cite a paper for a specific result or method: verify that result/method actually appears in the paper.

**Common errors to catch**:
- Citing paper A for a result that is actually from paper B
- Citing a survey when you should cite the original work
- Citing a preprint version when a published version exists (prefer published)
- Citing retracted papers

### Step 5: Add with Consistent Key Format

Use the citation key format: `author_year_firstword`

Examples:
- `vaswani_2017_attention` — "Attention Is All You Need" (Vaswani et al., 2017)
- `devlin_2019_bert` — "BERT: Pre-training of Deep Bidirectional Transformers" (Devlin et al., 2019)
- `brown_2020_language` — "Language Models are Few-Shot Learners" (Brown et al., 2020)

Rules for the key:
- `author`: first author's last name, lowercase
- `year`: publication year (4 digits)
- `firstword`: first meaningful word of the title, lowercase (skip articles: a, an, the)
- If duplicate key: append `_b`, `_c` etc.

## Batch Verification Workflow

When verifying all citations in a paper (e.g., during S6 Phase 4):

1. Extract all `\cite{key}` from .tex files.
2. For each key, find the corresponding `bibliography.bib` entry.
3. Run Steps 1-4 on each entry.
4. Flag any entry that fails Step 2 (cannot be confirmed in 2 sources).
5. Replace or remove flagged entries.
6. Verify no orphan citations (cited but not in .bib) or orphan entries (in .bib but not cited).

## Red Flags

These patterns indicate likely hallucinated citations:
- Paper title sounds too perfect for your argument
- You "remember" the paper but can't find it via search
- The paper has a very generic title
- Author names don't match any real researcher in the field
- The venue doesn't exist or didn't have proceedings that year

**When in doubt: search first, cite only if found.**
