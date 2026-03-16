# S1 Literature Survey — Multi-Source Literature Review

> Stage 1. Deep literature survey to establish baselines and identify gaps.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S1`. Note `papers_reviewed` counter.
2. Read `config.yaml` — check for `semantic_scholar_key`.
3. Read `RESEARCH_PROPOSAL.md` — extract research question, hypothesis, proposed method, baselines.
4. Read `.ai/core/research-context.md` — current research context.
5. Read `.ai/core/literature.md` — any prior findings (from P0 novelty check).
6. Read `bibliography.bib` if it exists — papers already found.
7. Check `state/JUDGE_RESULT.json` — if retrying:
   - Read `retry_guidance` to see what was insufficient.
   - Common issues: too few papers, missing baselines, gap not clearly stated.
   - Build on existing RELATED_WORK.md rather than starting over.

### Idempotency Check
- If `RELATED_WORK.md`, `BASELINES.md`, and `bibliography.bib` all exist and are complete:
  - Count papers in RELATED_WORK.md. If >= 20 and baselines >= 3, verify quality and skip.
  - If a retry, focus only on the failed criteria.

## Your Role

You are a thorough literature reviewer. You search multiple sources, read abstracts and key findings, cluster papers into themes, identify baselines with reported numbers, and produce a structured survey.

## Process

### Step 1: Formulate Search Queries

From RESEARCH_PROPOSAL.md, create 8-12 search queries covering:
1. The exact research question keywords
2. The proposed method name/type
3. Each baseline mentioned in the proposal
4. The target dataset or task
5. Key technical components of the proposed approach
6. Broader field surveys (e.g., "survey {topic}")
7. Recent work (add "2023 2024 2025" to key queries)
8. Alternative terminology for the same concepts

### Step 2: Search Semantic Scholar

For each query:
```bash
python3 scripts/scholarly_search.py search "<query>" --limit 20
```

Collect all unique papers. De-duplicate by title/DOI. Target: 50+ candidate papers.

If `scholarly_search.py` fails or returns too few results:
- Try rephrased queries.
- Fall back to web search for recent papers.
- Log the limitation but continue.

### Step 3: Search arXiv (supplementary)

Use web search with `site:arxiv.org` for:
- Very recent preprints (last 6 months)
- Workshop papers not yet in Semantic Scholar
- Related survey papers

### Step 4: Read and Classify

For each of the 50+ candidate papers, read the abstract (and intro/conclusion where available):

Classify relevance:
- **Core** (directly addresses the same question or method): Flag for deep reading
- **Related** (addresses a similar question or uses a similar method): Include in survey
- **Peripheral** (shares a keyword but different focus): Include only if filling a gap

For each paper, note:
- Title, authors, year, venue
- Key contribution (1 sentence)
- Method type
- Reported results (if applicable to our metrics)
- Relevance classification

### Step 5: Cluster into Themes

Group the papers into 3-5 thematic clusters. For each cluster:
- Name the theme
- Write a 2-3 paragraph summary of the research landscape
- Identify the progression of ideas within the theme
- Note what remains unsolved

### Step 6: Identify Baselines

From the papers, extract standard baselines:
- At least 3 baselines (judge requirement)
- For each baseline: method description, reported numbers on relevant metrics, paper reference
- Note if open-source code is available
- Note the dataset and evaluation protocol used

### Step 7: Flag Top-10 for Deep Reading

Select the 10 most relevant papers. For each:
- Full citation
- Why it is critical to read
- What specific information to extract during deep reading

### Step 8: State the Research Gap

Write a clear 2-3 paragraph statement of:
- What existing work does well
- What it does NOT address (the gap)
- How the proposed research fills this gap
- Why this gap matters

## Output Files

### RELATED_WORK.md

Use the template from `templates/RELATED_WORK.md`. Structure:

```markdown
# Related Work

## Theme 1: {Theme Name}
{Summary paragraphs}

### Key Papers
- [{Author}, {Year}] "{Title}" — {1-sentence summary}
- ...

## Theme 2: {Theme Name}
...

## Standard Baselines
| Baseline | Method | Dataset | Metric | Value | Source |
|----------|--------|---------|--------|-------|--------|

## Identified Gap
{Clear statement of the gap}

## Top-10 Papers for Deep Reading
1. ...
```

### BASELINES.md

Use the template from `templates/BASELINES.md`. For each baseline:

```markdown
## Baseline N: {Name}
- **Paper**: [{Author}, {Year}]
- **Method**: {brief description}
- **Reported Results**:
  - {metric}: {value}
- **Implementation Notes**: {reproduction details}
- **Code Available**: {URL or "no"}
```

### bibliography.bib

BibTeX entries for ALL cited papers. Every paper mentioned in RELATED_WORK.md or BASELINES.md MUST have an entry. Format:

```bibtex
@inproceedings{key,
  title={...},
  author={...},
  booktitle={...},
  year={...}
}
```

## .ai/ Updates

| File | Action |
|------|--------|
| `.ai/core/literature.md` | (updated by memory_sync — do not write directly) |

## Quality Criteria (from PIPELINE.md)

- [ ] >= 20 papers reviewed with proper citations
- [ ] >= 3 baselines identified with reported numbers
- [ ] Research gap clearly stated connecting to the research question
- [ ] All citations traceable to real papers (anti-hallucination)

## Anti-Hallucination Enforcement

- Every paper listed MUST have been returned by a search query or web search.
- Cross-reference: if you mention a paper in RELATED_WORK.md, it must be in bibliography.bib.
- If a paper's details are uncertain, search for it again to verify.
- Do not fill in venue or year from memory — extract from search results only.

## Rules

- Prefer breadth in the initial search, depth in the top-10 selection.
- Be honest about search coverage — if a sub-area has few results, note it.
- Do not editorialize — report findings objectively.
- Do not propose hypotheses — that is S2's job.
- If fewer than 20 papers are found after exhaustive search, document the search queries tried and report the limitation. The field may genuinely be under-explored.

## When Done

- `RELATED_WORK.md` exists with >= 20 papers organized by theme.
- `BASELINES.md` exists with >= 3 baselines and reported numbers.
- `bibliography.bib` exists with entries for all cited papers.
- `.ai/core/literature.md` is updated.
- Commit: `S1: literature survey — {N} papers, {M} baselines, {K} themes`
- Commit: `docs(.ai): update literature context from S1 survey`
