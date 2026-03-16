# VLM Review — Scientific Figure Quality Assessment

> Invoked after figure generation to assess publication quality.
> Inherits: `_common.md`

## Before You Start

1. Identify the figure to review. Input: figure file path (e.g., `results/H1_R1/figures/learning_curve.png`).
2. Check `state/VLM_REVIEW_{figure_name}.json` — if it exists:
   - Read the current attempt count.
   - If attempt >= 3 and score < 4: this figure has failed max attempts. Flag for human review.
   - If score >= 4: figure already approved. Skip.
3. Read the figure's context:
   - What experiment produced it (from experiment_tree.json or the results directory).
   - What point it is supposed to illustrate (from EXPERIMENT_PLAN.md or ANALYSIS.md).

## Your Role

You review scientific figures for publication quality. You score on 5 criteria and provide actionable feedback for regeneration if the figure does not meet the quality bar.

## Process

### Step 1: View the Figure

Read the figure file. Examine it carefully for:
- Visual clarity
- Information content
- Technical correctness
- Aesthetic quality
- Accessibility

### Step 2: Score on 5 Criteria

Rate each criterion from 1-5:

**1. Readability (1-5)**
- 1: Unreadable — text too small, overlapping elements, no labels
- 2: Poor — some labels missing or hard to read
- 3: Acceptable — readable but requires effort
- 4: Good — clear labels, appropriate font sizes, no overlap
- 5: Excellent — immediately clear, well-organized layout

**2. Information Density (1-5)**
- 1: Empty — conveys almost no information
- 2: Sparse — could show much more
- 3: Adequate — shows the main point
- 4: Rich — multiple insights visible
- 5: Optimal — maximum information without clutter

**3. Technical Correctness (1-5)**
- 1: Incorrect — wrong axis labels, wrong data, misleading
- 2: Errors — some values wrong or misleading presentation
- 3: Mostly correct — minor issues (e.g., missing units)
- 4: Correct — accurate representation of data
- 5: Rigorous — error bars, proper scaling, no misleading presentation

**4. Aesthetic Quality (1-5)**
- 1: Ugly — default matplotlib with no styling
- 2: Poor — inconsistent colors, bad proportions
- 3: Acceptable — clean but unremarkable
- 4: Professional — consistent styling, good color palette
- 5: Publication-ready — matches top venue standards

**5. Accessibility (1-5)**
- 1: Inaccessible — relies entirely on color with no alternatives
- 2: Poor — color-dependent with no consideration for colorblindness
- 3: Adequate — some effort at accessibility
- 4: Good — color-blind friendly palette, patterns/markers used
- 5: Excellent — fully accessible, multiple visual channels

### Step 3: Compute Overall Score

```
overall = mean(readability, information_density, technical_correctness, aesthetic_quality, accessibility)
```

Round to 1 decimal place.

### Step 4: Decision

| Overall Score | Decision |
|--------------|----------|
| >= 4.0 | **APPROVED** — figure meets publication quality |
| 3.0-3.9 | **REVISE** — specific improvements needed |
| < 3.0 | **REJECT** — fundamental issues, likely needs redesign |

### Step 5: Generate Feedback (if score < 4.0)

For each criterion scoring below 4, provide specific, actionable feedback:

```markdown
### Readability (score: 2)
- Font size on x-axis labels is too small (appears to be ~8pt). Increase to at least 12pt.
- Legend overlaps with data points in the upper-right. Move legend outside the plot or to an empty area.

### Technical Correctness (score: 3)
- Missing error bars on the bar chart. Add standard deviation or 95% CI bars.
- Y-axis does not start at a meaningful baseline — consider starting at 0 or clearly marking the axis break.
```

Include specific regeneration instructions:
```markdown
### Regeneration Instructions
1. Increase all font sizes to >= 12pt
2. Add error bars (standard deviation)
3. Move legend to lower-right corner
4. Use colorblind-safe palette: ['#0072B2', '#D55E00', '#009E73', '#CC79A7']
5. Set DPI to 300
6. Add gridlines (alpha=0.3) for readability
```

### Step 6: Write State

Write `state/VLM_REVIEW_{figure_name}.json`:

```json
{
  "figure_path": "results/H1_R1/figures/learning_curve.png",
  "figure_name": "learning_curve",
  "attempt": N,
  "scores": {
    "readability": X,
    "information_density": X,
    "technical_correctness": X,
    "aesthetic_quality": X,
    "accessibility": X
  },
  "overall": X.X,
  "decision": "APPROVED" | "REVISE" | "REJECT",
  "feedback": "...",
  "regeneration_instructions": "...",
  "timestamp": "..."
}
```

If this is a re-review (attempt > 1), also include:
```json
{
  "improvement_from_previous": {
    "previous_overall": X.X,
    "current_overall": X.X,
    "improved_criteria": ["readability", "accessibility"],
    "unchanged_criteria": ["technical_correctness"]
  }
}
```

## Output

| File | Action |
|------|--------|
| `state/VLM_REVIEW_{figure_name}.json` | Write review result |

## Regeneration Protocol

When a figure is rejected or needs revision:

1. The calling skill (S4_run_node, S5_analysis, or S6_writing) reads the feedback.
2. The calling skill regenerates the figure following the regeneration instructions.
3. The calling skill re-invokes this VLM review skill on the new figure.
4. Maximum 3 attempts total.
5. After 3 failed attempts:
   - Keep the best version (highest overall score across attempts).
   - Flag for human review in the state file.
   - The calling skill proceeds with the best available version.

## Publication Quality Standards

For top-venue publication (NeurIPS, ICML, ICLR, ACL, etc.):
- Minimum font size: 12pt in figure, matching paper body text
- DPI: >= 300 for raster, vector preferred (PDF/SVG)
- Color palette: colorblind-safe (e.g., Okabe-Ito, Tol, or seaborn colorblind)
- Error bars: required for any stochastic results
- Axis labels: descriptive, with units where applicable
- Legend: clear, not overlapping data
- Grid: optional but helpful for comparison charts
- Aspect ratio: appropriate for the data type
- White space: balanced, not too cramped or too sparse

## Rules

- Be honest in scoring. A bad figure is a bad figure regardless of how good the results are.
- Provide constructive feedback — every criticism must include how to fix it.
- Do not approve figures out of convenience. The paper quality depends on figure quality.
- Consider the figure in context — a learning curve has different requirements than a comparison bar chart.
- If the data itself is problematic (e.g., clearly wrong values), flag this as a technical correctness issue AND notify the calling skill.

## When Done

- State file written with scores and decision.
- If APPROVED: calling skill proceeds with the figure.
- If REVISE/REJECT: calling skill reads feedback and regenerates.
- No commit needed — state/ is not committed.
