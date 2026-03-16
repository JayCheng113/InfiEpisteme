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

### Idempotency Check
- If `paper.pdf` exists and compiles cleanly, and no retry: verify completeness and skip.
- If partial (some sections exist): write only missing sections.

## Your Role

You write a complete research paper in LaTeX, section by section, then compile to PDF. You write in clear academic English and ensure every claim is backed by data or citation.

## Process

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

### Phase 4: Anti-Hallucination Citation Verification

Before compilation, verify EVERY citation:

1. Extract all `\cite{key}` from all .tex files.
2. For each key, verify it exists in `bibliography.bib`.
3. For each bibliography entry, verify it refers to a real paper:
   - Check via `python3 scripts/scholarly_search.py search "{title}"` or web search.
   - Verify: title, authors, year, venue match.
4. Remove or fix any phantom citations.
5. Check for uncited bibliography entries (warn but do not remove — they may be used in appendix).

### Phase 5: Compile

1. Set up paper structure:
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
   - If compilation fails: read the log, fix the error, retry (max 3 attempts).
   - Common fixes: undefined references (run bibtex again), missing packages (add \usepackage), figure not found (check path).

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

## When Done

- `paper.pdf` exists and is a valid PDF.
- All sections are complete and cross-referenced.
- All citations verified against real papers.
- Commit: `S6: paper written and compiled — {page_count} pages`
