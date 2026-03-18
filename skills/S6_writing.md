# S6 Writing — Paper Composition and Compilation

> Stage 6. Multi-phase paper writing from plan to compiled PDF.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S6`.
2. Read `config.yaml` — target venue for formatting.
3. Read ALL input documents:
   - `RESEARCH_PROPOSAL.md` — research question, hypothesis
   - `RELATED_WORK.md` — literature survey for Section 2
   - `EXPERIMENT_PLAN.md` — method details for Section 3
   - `RESULTS_SUMMARY.md` — results for Section 4
   - `ANALYSIS.md` — statistical analysis for Section 4-5
   - `bibliography.bib` — references
4. Read `.ai/` context:
   - `.ai/core/research-context.md`
   - `.ai/core/methodology.md`
   - `.ai/core/literature.md`
   - `.ai/evolution/decisions.md`
5. Check `state/JUDGE_RESULT.json` — if retrying:
   - Common issues: LaTeX compilation errors, missing figures, phantom citations.
   - Fix the specific issues flagged.

### Writing References
- **ML paper writing best practices**: Read `skills/references/writing-guide.md` for narrative principles, abstract formula, and writing style
- **Academic writing style**: Read `skills/references/academic-writing-style.md` for word choice, hedging, tense usage, and common errors
- **LaTeX debugging**: Read `skills/references/latex-debugging.md` for error patterns, silent failures, package load order, and long-form document rules
- **Citation verification protocol**: Read `skills/references/citation-verification.md` (already required)

### Idempotency Check
- If `paper.pdf` exists and compiles cleanly, and no retry: verify completeness and skip.
- If partial (some sections exist): write only missing sections.

## Your Role

You write a complete research paper in LaTeX, section by section, then compile to PDF. You write in clear academic English and ensure every claim is backed by data or citation.

## Process

### Phase 0: Determine What Story the Data Supports

Before planning or writing anything, read `ANALYSIS.md` and `RESULTS_SUMMARY.md` carefully. Then answer:

1. **What is the single most important finding?** Not what you hoped to find — what the data actually shows.
2. **What type of paper does the data support?**
   - Strong positive result → "We propose X, which outperforms Y because Z"
   - Mixed result → "Under conditions A, X works; under B, Y works — here's why"
   - Negative/null result → "Contrary to expectation, X does not improve over Y — analysis reveals Z"
   - Benchmark/empirical study → "We provide the first controlled comparison of methods A-F and find..."
3. **What claims can you actually make?** List only claims directly supported by your experimental evidence. Do not claim more than the data shows.
4. **What is the narrative arc?** Problem → gap → approach → results → insight. The arc depends on the findings, not on a template.

The paper structure below is a starting point. Adapt it based on your answers — a negative result paper emphasizes analysis over method description; a benchmark paper emphasizes experimental setup and fairness over novelty.

### Phase 1: Plan

Before writing any LaTeX, create a paper plan:

**Claims Matrix**: For each claim the paper makes:
| Claim | Evidence | Location in Paper | Supporting Data |
|-------|---------|-------------------|----------------|
| "Our method outperforms X on Y" | Table 1 | Section 4.2 | results/H1_R1_C2/metrics.json |

**Section Structure**:
1. Abstract (written last)
2. Introduction: problem + gap + contributions
3. Related Work: organized by theme
4. Method: approach description with formal notation
5. Experiments: setup, main results, ablations, analysis
6. Conclusion: summary + limitations + future work

**Figure Plan**: List every figure with:
- Figure number, caption draft, source file
- Where it appears in the paper
- What point it supports

### Phase 2: Figures

1. Collect all approved figures from:
   - `results/*/figures/` — experiment figures
   - `figures/analysis/` — analysis figures
2. Copy or symlink to `paper/figures/`.
3. For any missing figures identified in the figure plan:
   - Generate with matplotlib (publication quality: DPI >= 300, font >= 12pt)
   - Submit for VLM review
   - Iterate until approved (max 3 attempts)
4. Create a figure index: `paper/figures/index.md` listing all figures and their paper locations.

### Phase 3: Write Sections

Write in this order (not the order they appear in the paper):

**3a. Section 3: Method** (from EXPERIMENT_PLAN.md + methodology.md)
- Problem formulation with notation
- Proposed approach with mathematical detail
- Key design decisions and their rationale
- Connection to prior work (how this extends/differs)

**3b. Section 4: Experiments** (from RESULTS_SUMMARY.md + ANALYSIS.md)
- Experimental setup: datasets, metrics, baselines, implementation details
- Main results table with discussion
- Ablation study with analysis
- Qualitative examples or case studies
- Error analysis summary

**3c. Section 2: Related Work** (from RELATED_WORK.md, reorganized for narrative)
- Organize by theme, not alphabetically
- Position our work relative to each thread
- End with a clear statement of our contribution's novelty

**3d. Section 1: Introduction**
- Opening: motivate the problem (1-2 paragraphs)
- Gap: what existing work misses (1 paragraph)
- Our approach: high-level description (1 paragraph)
- Contributions: bulleted list (3-4 items)
- Paper organization (optional, 1 sentence)

**3e. Section 5: Conclusion**
- Summary of contributions and key results
- Limitations (be honest)
- Future work directions
- Broader impact (if relevant for the venue)

**3f. Abstract** (written last — summarizes everything)
- Problem (1 sentence)
- Gap (1 sentence)
- Approach (1-2 sentences)
- Key result (1 sentence)
- Significance (1 sentence)
- Target: 150-250 words

### Phase 4: Anti-Hallucination Citation Verification (5-Step Protocol)

Before compilation, verify EVERY citation using the full 5-step protocol from `skills/references/citation-verification.md`:

1. **Search**: Extract all `\cite{key}` from .tex files. For each bibliography entry, search for the paper title using Semantic Scholar MCP (`mcp__semantic-scholar__search_papers`) or fallback (`python3 scripts/scholarly_search.py search "{title}"`).

2. **Verify (2+ sources)**: Confirm each paper exists in at least 2 independent sources (Semantic Scholar + arXiv/CrossRef/DBLP). Check that title, first author, year, and venue match across sources. **If a paper cannot be confirmed in 2 sources: REMOVE the citation.**

3. **Retrieve BibTeX**: Get BibTeX from Semantic Scholar MCP (`mcp__semantic-scholar__get_paper_details`) or DOI lookup. **Never generate BibTeX from LLM memory.** Replace any hand-written BibTeX with authoritative versions.

4. **Validate context**: For each citation, verify the paper's actual content supports the claim you're making. Read at least the abstract to confirm relevance. Common errors: citing paper A for a result from paper B, citing surveys instead of original work.

5. **Add with consistent keys**: Ensure all citation keys follow `author_year_firstword` format (e.g., `vaswani_2017_attention`). Fix any inconsistent keys.

After verification:
- Remove or fix any phantom citations (cited but not in .bib).
- Check for uncited bibliography entries (warn but do not remove — they may be used in appendix).
- Log the verification: "{N} citations verified, {M} removed as unverifiable."

### Phase 4.5: Incremental Compilation (after each section)

**Do not wait until all sections are written to compile.** After writing each section file, compile immediately:

```bash
cd paper && pdflatex -interaction=nonstopmode main.tex 2>&1 | tail -20
```

If compilation fails:
1. Search for `!` in the output or log file — these are actual errors (the rest is noise).
2. Fix the **first** error only, then recompile — early errors cascade into false errors downstream.
3. Consult `skills/references/latex-debugging.md` for the 20 most common errors and silent failures.
4. Watch for **silent failures** that compile but produce wrong output: angle brackets as `¡¿`, empty bibliography, misplaced figures.
5. Only proceed to the next section after this one compiles cleanly.

This catches errors immediately when context is fresh, rather than debugging a pile of errors at the end.

### Phase 5: Final Compile and Verify

1. Set up paper structure (should already exist from incremental compilation):
```
paper/
  main.tex          # master file with \input{} for each section
  sections/
    abstract.tex
    introduction.tex
    related_work.tex
    method.tex
    experiments.tex
    conclusion.tex
  figures/           # approved figures
  bibliography.bib   # copy from root
```

2. Write `paper/main.tex` with appropriate document class:

   **Template Selection** (based on config.yaml target_venue):
   - If target_venue contains "NeurIPS": use `templates/latex/neurips2025.tex` as base
   - If target_venue contains "ICML": use `templates/latex/icml2025.tex` as base
   - If target_venue contains "ICLR": use `templates/latex/iclr2026.tex` as base
   - Otherwise: use standard `article` class

   Copy the selected template to `paper/main.tex` and adapt it (replace placeholder sections with \input{sections/...}).
   Include `templates/latex/math_commands.tex` via \input if it exists.

   - Include all standard packages: amsmath, graphicx, booktabs, hyperref, natbib/biblatex

3. Compile:
```bash
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

4. Check for errors:
   - If compilation fails: read `paper/main.log`, search for lines starting with `!` (these are the actual errors). Fix and retry.
   - If bibtex fails: check `paper/main.blg` for missing entries or format errors.
   - Max 5 fix-compile cycles. If still failing after 5, report the specific error — do not silently produce a broken PDF.

5. Copy final PDF:
```bash
cp paper/main.pdf paper.pdf
```

6. Verify PDF:
   - Page count > 0
   - All figures visible
   - All tables rendered
   - No "??" undefined references
   - Bibliography renders correctly

## Output

| File | Action |
|------|--------|
| `paper/main.tex` | Create master LaTeX file |
| `paper/sections/*.tex` | Create section files |
| `paper/figures/` | Populate with approved figures |
| `paper/bibliography.bib` | Copy from root |
| `paper.pdf` | Compiled paper |

## Quality Criteria (from PIPELINE.md)

- [ ] LaTeX compiles without errors (pdflatex exit code 0)
- [ ] PDF renders correctly (page count > 0)
- [ ] All figures referenced in text are present in paper/figures/
- [ ] All citations in text have corresponding bibliography entries
- [ ] No hallucinated citations (every \cite{} matches a real bibliography.bib entry)

## Writing Rules

- Write in clear, concise academic English. No filler words.
- Every claim must be backed by data (table/figure reference) or citation.
- Do not overstate results — use precise language ("improves by 3.2%" not "dramatically improves").
- Report limitations honestly in the conclusion.
- Use consistent notation throughout all sections.
- Define notation on first use.
- Use booktabs style for tables (\toprule, \midrule, \bottomrule).
- All figures must have informative captions.
- Number formatting: use consistent decimal places, proper significant figures.

## Citation Coverage Rules

- **Minimum 30 citations** in the final paper. A 10+ page paper with fewer than 30 citations signals inadequate literature coverage.
- **Recency requirement**: At least 3 citations from the current or previous year. A paper submitted in 2026 with no 2025-2026 citations looks outdated.
- **All papers from RELATED_WORK.md and BASELINES.md** should be cited somewhere in the paper. Do not drop references between S1 and S6.
- **Every related work theme** must cite at least 3 papers. Single-citation themes suggest superficial coverage.
- If bibliography.bib has fewer than 30 entries, go back to RELATED_WORK.md and add missing references before writing.

## When Done

- `paper.pdf` exists and is a valid PDF.
- All sections are complete and cross-referenced.
- All citations verified against real papers.
- Commit: `S6: paper written and compiled — {page_count} pages`
