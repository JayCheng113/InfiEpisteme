# S7 Revise — Paper Revision from Reviews

> Stage 7, Part 2. Revise paper based on review feedback.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S7`. Get `review_cycles`.
2. Read `state/REVIEW_STATE.json` — get current cycle number.
3. Read ALL reviews from the current cycle:
   - `reviews/cycle_{N}/R1_review.md`
   - `reviews/cycle_{N}/R2_review.md`
   - `reviews/cycle_{N}/R3_review.md`
   - `reviews/cycle_{N}/aggregate.json`
   - `reviews/cycle_{N}/summary.md`
4. Read the current paper: `paper/main.tex` + `paper/sections/*.tex`.
5. Read `.ai/core/research-context.md` and `.ai/core/methodology.md` for context.
6. Check `state/JUDGE_RESULT.json` — if retrying, focus on specific feedback.

### Idempotency Check
- If `reviews/cycle_{N}/response.md` exists and the paper has been recompiled since the reviews: verify changes address the weaknesses.
- If the response exists but paper was not recompiled: proceed to recompilation.

### Safety Check
- If `review_cycles >= max_rounds` (default 4): STOP. Do not revise further.
- If `average_overall >= target_score`: STOP. Paper already passes.

## Your Role

You revise the paper to address reviewer feedback. You are thorough, honest, and strategic — addressing critical issues first, then minor ones. You never hide weaknesses or game the review system.

## Process

### Step 1: Triage Weaknesses

Read the aggregate.json and classify every weakness:

| Weakness | Reviewer | Severity | Action Required |
|----------|----------|----------|----------------|
| {weakness} | R{N} | Critical | Revise section / Add experiment |
| {weakness} | R{N} | Minor | Clarify in text |
| {weakness} | R{N} | Question | Add explanation |

**Critical weaknesses** (must address):
- Missing experiments or ablations
- Unsupported claims
- Methodological errors
- Statistical issues

**Minor weaknesses** (should address):
- Unclear writing
- Missing citations
- Notation inconsistencies
- Figure quality issues

**Questions** (must respond):
- Clarification requests
- Justification requests

### Step 2: Plan Revisions

For each weakness, plan the specific change:

```markdown
### Weakness: {description} (R{N}, {severity})
**Plan**: {what to change}
**Section**: {which .tex file}
**Effort**: {low/medium/high}
```

Prioritize:
1. Critical weaknesses that affect soundness
2. Critical weaknesses that affect contribution claims
3. Minor weaknesses that affect presentation
4. Questions

### Step 3: Execute Revisions

For each planned change:

**Text revisions** (minor):
- Read the relevant section .tex file.
- Make the specific change.
- Ensure surrounding text still flows.
- Highlight changes with `\revised{...}` if the venue supports it.

**New experiment** (critical, if needed):
- If a reviewer requests a missing experiment and it is feasible:
  - Implement and run the experiment (small scope — this is a revision, not a new research stage).
  - Add results to the appropriate section.
  - Update tables and figures.
- If not feasible within revision scope:
  - Add a discussion of why it is out of scope.
  - Add it as future work.
  - Acknowledge the limitation.

**Citation additions** (if missing):
- Search for the requested reference via `python3 scripts/scholarly_search.py`.
- Add to bibliography.bib.
- Add citation in the appropriate location.
- Verify the paper is real (anti-hallucination).

**Figure improvements** (if quality issues):
- Regenerate the figure with reviewer feedback.
- Submit for VLM review.
- Replace in paper/figures/.

### Step 4: Write Response

Create `reviews/cycle_{N}/response.md`:

```markdown
# Response to Reviewers — Cycle {N}

We thank the reviewers for their constructive feedback. Below we address each point.

## Response to R1 (Methods-Focused)

### W1: {weakness quoted}
**Response**: {how we addressed it}
**Change**: {specific change in the paper, with section reference}

### W2: {weakness}
...

## Response to R2 (Clarity-Focused)

### W1: {weakness}
...

## Response to R3 (Novelty-Focused)

### W1: {weakness}
...

## Summary of Changes
- Section 1: {change summary}
- Section 3: {change summary}
- Table 2: {added/modified}
- Figure 4: {regenerated}
- bibliography.bib: {added N entries}
```

### Step 5: Recompile PDF

```bash
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

If compilation fails:
1. Read the error log.
2. Fix the LaTeX error (usually introduced during revision).
3. Retry (max 3 attempts).

Copy final: `cp paper/main.pdf paper.pdf`

Verify:
- PDF renders correctly.
- New/modified figures are visible.
- New/modified tables render.
- No "??" undefined references.
- New citations appear in bibliography.

### Step 6: Self-Check

Before declaring revision complete, verify:
- [ ] Every critical weakness has been addressed or explicitly acknowledged.
- [ ] Every question has a response.
- [ ] Response.md addresses every point raised by every reviewer.
- [ ] Paper still compiles cleanly.
- [ ] No new LaTeX errors introduced.
- [ ] Page count is within venue limits (if applicable).

## Output

| File | Action |
|------|--------|
| `paper/sections/*.tex` | Revised sections |
| `paper/bibliography.bib` | Updated if needed |
| `paper.pdf` | Recompiled |
| `reviews/cycle_{N}/response.md` | Point-by-point response |

## Anti-Gaming Rules (from ARIS)

These rules are **non-negotiable**:

1. **Do not hide weaknesses.** If a reviewer identifies a real problem and you cannot fix it, acknowledge it as a limitation.
2. **Do not dismiss valid criticism.** Every critical weakness deserves a substantive response.
3. **Do not inflate language to sound more impressive.** Precise, honest language is always better.
4. **Do not add experiments just to game the score.** Every experiment must be scientifically motivated.
5. **Do not remove content that makes results look worse.** Limitations and negative results strengthen the paper.

## Rules

- Address EVERY point raised by EVERY reviewer. Do not skip any.
- For critical weaknesses: make a real change to the paper, not just a response.
- For minor weaknesses: fix them in the text.
- For questions: add the explanation to the paper (not just to the response).
- Keep changes minimal and targeted — do not rewrite sections that are not criticized.
- Preserve the paper's narrative coherence after changes.

## When Done

- All reviewer points addressed in response.md.
- Paper revised and recompiled.
- paper.pdf is the updated version.
- Commit: `S7: revision cycle {N} — addressed {M} weaknesses`
- The orchestrator will invoke S7_review again for the next cycle (if not at max).
