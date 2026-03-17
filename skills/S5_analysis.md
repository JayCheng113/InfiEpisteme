# S5 Analysis — Statistical Analysis and Multi-Perspective Interpretation

> Stage 5. Rigorous statistical analysis with multi-perspective result interpretation.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S5`.
2. Read `RESULTS_SUMMARY.md` — main results and ablation table.
3. Read `experiment_tree.json` — full tree with all node results.
4. Read `BASELINES.md` — baseline reported numbers for comparison.
5. Read `EXPERIMENT_PLAN.md` — evaluation protocol, metrics definitions.
6. Read `.ai/core/methodology.md` — approach details for interpretation.
7. Read `.ai/core/literature.md` — context for competitive comparison.
8. Read `.ai/evolution/negative-results.md` — failed experiments for context.
9. Check `state/JUDGE_RESULT.json` — if retrying, focus on:
   - Missing significance tests
   - Missing error analysis
   - Incomplete multi-perspective analysis

### Evaluation References
- **Standardized LLM benchmarks**: Read `skills/references/impl-lm-eval.md` for lm-evaluation-harness setup and benchmark selection

### Idempotency Check
- If `ANALYSIS.md` exists with complete statistical tests: verify and skip.
- If partial: complete the missing sections.

## Your Role

You perform rigorous statistical analysis and provide multi-perspective interpretation of the experimental results. You are skeptical, thorough, and honest about what the numbers say.

## Process

### Step 1: Collect All Results

Gather metrics from:
- `results/{node_id}/metrics.json` for all completed nodes
- Baseline results from BASELINES.md
- Ablation results from Stage 4.4

Organize into a master results table with all methods and all metrics.

### Step 2: Statistical Significance Tests

For each main comparison (proposed method vs. each baseline):

**Paired t-test** (if multiple test instances):
- Null hypothesis: no difference in performance
- Report: t-statistic, p-value, degrees of freedom
- Significance threshold: p < 0.05

**Bootstrap confidence intervals** (95%):
- 10,000 bootstrap resamples
- Report: mean, 95% CI lower bound, 95% CI upper bound
- For the primary metric and key secondary metrics

**Effect size**:
- Cohen's d for each comparison
- Practical significance assessment

Write code to compute these and save results:
```python
# Save to results/statistical_tests.json
{
  "comparisons": [
    {
      "method_a": "ours",
      "method_b": "baseline_1",
      "metric": "primary_metric",
      "t_statistic": ...,
      "p_value": ...,
      "cohens_d": ...,
      "ci_95": [lower, upper],
      "significant": true/false
    }
  ]
}
```

### Step 3: Multi-Perspective Analysis

Analyze results from 6 viewpoints. You adopt each perspective in turn.

**Perspective 1: Optimist**
Focus: positive signal extraction.
- What are the strongest results?
- Where does the method clearly outperform?
- What is the most impressive finding?
- What story do these results tell?

**Perspective 2: Skeptic**
Focus: statistical rigor, alternative explanations.
- Are the improvements statistically significant?
- Could the improvements be due to chance, hyperparameter tuning, or data leakage?
- Are there confounding variables?
- Are the baselines fairly compared (same data, same compute, same tuning)?
- Is the evaluation protocol sound?
- Do the numbers seem too good? Check for common pitfalls.

**Perspective 3: Strategist**
Focus: resource-efficient next steps.
- What would improve results most with the least additional compute?
- Which experiments had the best return on GPU-hours?
- Where should resources be invested for the next iteration?

**Perspective 4: Methodologist**
Focus: protocol soundness.
- Is the evaluation protocol standard for this field?
- Are the metrics appropriate for the claims being made?
- Are train/val/test splits proper (no leakage)?
- Is the comparison fair?

**Perspective 5: Comparativist**
Focus: competitive benchmarking.
- How do our results compare to state-of-the-art (from literature)?
- Are we using the same evaluation protocol as prior work?
- Where do we rank in the competitive landscape?
- Are there important baselines we missed?

**Perspective 6: Revisionist**
Focus: hypothesis refinement.
- Did the original hypotheses hold? Fully, partially, or not at all?
- What did we learn that we did not expect?
- Should we refine the hypothesis based on evidence?
- What new questions arise from these results?

### Step 4: Error Analysis

1. **Categorize failure modes**:
   - Collect all instances where the method underperforms
   - Group by failure type (e.g., "fails on long sequences", "fails on rare categories")
   - Compute failure rate per category
   - Identify the top-3 failure modes by frequency

2. **Root cause analysis**:
   - For each top failure mode, hypothesize the root cause
   - Check if ablation results support or contradict the hypothesis
   - Suggest specific fixes for each failure mode

3. **Comparison with baselines**:
   - Do baselines fail in the same ways?
   - Where does our method fail but baselines succeed (and vice versa)?
   - Is there complementary behavior suggesting ensemble potential?

### Step 5: Qualitative Case Studies

Select 3-5 representative examples:
- 2-3 where the method succeeds (showing clear advantage)
- 1-2 where the method fails (showing limitations)

For each case study:
- Describe the input/scenario
- Show method output vs. baseline output
- Explain why the method succeeded or failed
- What this reveals about the approach

### Step 6: Generate Analysis Figures

Create publication-quality figures:
1. **Results comparison bar chart** with error bars (confidence intervals)
2. **Ablation impact chart** showing component contributions
3. **Error analysis visualization** (confusion matrix, error distribution, etc.)
4. **Case study figures** if applicable
5. **Statistical significance heatmap** (method vs. method with p-values)

Save to `figures/analysis/`. Submit each for VLM review.

### Step 7: Generate LaTeX Tables

Create LaTeX-ready tables in `tables/`:
- `tables/main_results.tex` — main comparison table
- `tables/ablation.tex` — ablation study table
- `tables/significance.tex` — statistical significance results
- `tables/error_analysis.tex` — failure mode breakdown

Format: standard LaTeX tabular, ready for inclusion in paper.

## Output Files

### ANALYSIS.md

```markdown
# Analysis

## Statistical Significance
{Summary of significance test results}

### Detailed Results
| Comparison | t-stat | p-value | Cohen's d | 95% CI | Significant? |
|-----------|--------|---------|-----------|---------|-------------|

## Multi-Perspective Analysis

### Optimist View
{Positive signals and strongest results}

### Skeptic View
{Statistical concerns and alternative explanations}

### Strategist View
{Resource allocation recommendations}

### Methodologist View
{Protocol soundness assessment}

### Comparativist View
{Competitive landscape positioning}

### Revisionist View
{Hypothesis refinement based on evidence}

## Error Analysis

### Failure Mode Taxonomy
| Mode | Frequency | Root Cause | Suggested Fix |
|------|-----------|-----------|---------------|

### Detailed Analysis
{Per-mode deep dive}

## Case Studies

### Case 1: {Description}
{Detailed analysis}

...

## Key Takeaways
1. {takeaway}
2. {takeaway}
3. {takeaway}

## Limitations
{Honest assessment of what these results do NOT show}
```

### Other Outputs
- `tables/*.tex` — LaTeX tables
- `figures/analysis/` — analysis figures
- `results/statistical_tests.json` — raw statistical test results

## .ai/ Updates

| File | Action |
|------|--------|
| `.ai/evolution/decisions.md` | (updated by memory_sync — do not write directly) |

## Quality Criteria (from PIPELINE.md)

- [ ] Statistical significance tests run on all main comparisons
- [ ] P-values computed and reported with effect sizes
- [ ] Error analysis with categorized failure modes
- [ ] Multi-perspective analysis completed (6 viewpoints documented)
- [ ] All analysis figures VLM-approved

## Rules

- Never cherry-pick results. Report all comparisons, not just favorable ones.
- Use proper statistical methodology — no p-hacking, no selective reporting.
- Report effect sizes alongside p-values (statistical significance is not practical significance).
- Flag any results that seem too good to be true.
- Be honest about limitations — the paper will be stronger for it.
- If a hypothesis was wrong, say so clearly.
- Do not propose new experiments — that was S4's job. Analyze what you have.

## When Done

- `ANALYSIS.md` exists with all sections complete.
- `tables/` has LaTeX tables.
- `figures/analysis/` has VLM-approved figures.
- `results/statistical_tests.json` has raw test results.
- `.ai/evolution/decisions.md` has ADR-003.
- Commit: `S5: statistical analysis complete — {key finding summary}`
- Commit: `docs(.ai): record analysis decisions in ADR-003`
