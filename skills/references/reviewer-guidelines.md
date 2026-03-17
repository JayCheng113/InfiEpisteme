# Reviewer Evaluation Guidelines
> Reference for S7. Load when performing adversarial review or preparing rebuttal strategy.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## 4 Evaluation Dimensions

### 1. Quality
Is the paper technically sound?

| Aspect | Strong | Weak |
|--------|--------|------|
| Methodology | Well-motivated, formally justified | Ad-hoc, no justification for choices |
| Experiments | Multiple datasets, strong baselines, ablations | Single dataset, weak baselines |
| Analysis | Error analysis, failure cases discussed | Only positive results shown |
| Reproducibility | Full details provided, code promised | Missing hyperparameters, no code |
| Statistical rigor | Confidence intervals, multiple runs | Single run, no variance reported |

### 2. Clarity
Is the paper well-written and easy to follow?

| Aspect | Strong | Weak |
|--------|--------|------|
| Structure | Logical flow, each section builds on previous | Jumps between topics |
| Writing | Precise, concise, no jargon without definition | Vague, verbose, undefined terms |
| Figures | Self-contained captions, clear labels | Unreadable, missing labels |
| Notation | Consistent throughout | Changes meaning mid-paper |
| Motivation | Clear problem statement and why it matters | Unclear why anyone should care |

### 3. Significance
Does the paper advance the field?

| Aspect | Strong | Weak |
|--------|--------|------|
| Impact | Enables new research directions or applications | Marginal improvement on narrow task |
| Generality | Method applies broadly | Only works on one specific setting |
| Insight | Provides understanding of why something works | Black-box improvement, no analysis |
| Practical value | Can be adopted by practitioners | Requires unrealistic resources |

### 4. Originality
Is the contribution novel?

| Aspect | Strong | Weak |
|--------|--------|------|
| Novelty | New problem, method, or perspective | Straightforward combination of existing work |
| Differentiation | Clearly explains what is new vs. prior work | Unclear how it differs from [X] |
| Related work | Thorough, honest positioning | Missing key related papers |

## Scoring Rubric

| Score | Label | Criteria |
|-------|-------|----------|
| **10** | Top paper | Transformative. Will be widely cited. Flawless execution. |
| **8-9** | Strong accept | Major contribution. Novel, thorough, clear. Minor issues only. |
| **7** | Accept | Clear contribution to the field. Well-executed. Some minor weaknesses. |
| **6** | Weak accept | Solid work. Contribution is meaningful but not groundbreaking. Competent execution. |
| **5** | Borderline | Has merit but also notable weaknesses. Could go either way. |
| **4** | Weak reject | Below acceptance threshold. Incremental contribution or significant issues. |
| **3** | Reject | Fundamental issues: wrong methodology, insufficient experiments, or unclear contribution. |
| **1-2** | Strong reject | Fatally flawed. Major errors, inappropriate for venue, or not a research contribution. |

## Review Template

```markdown
## Summary
[2-3 sentences: what the paper does and its main claim]

## Strengths
1. [Most important strength]
2. [Second strength]
3. [Third strength]

## Weaknesses
1. [Most important weakness — be specific and constructive]
2. [Second weakness]
3. [Third weakness]

## Questions for Authors
1. [Specific question that could change your assessment]
2. [Clarification needed]

## Minor Issues
- [Typos, formatting, small suggestions]

## Overall Assessment
[1-2 sentences summarizing your recommendation]

## Scores
- Quality: X/10
- Clarity: X/10
- Significance: X/10
- Originality: X/10
- Overall: X/10
- Confidence: X/5
```

## Self-Review Checklist (Pre-Submission)

### Technical Soundness
- [ ] All proofs are correct (or at least checked by a second person)
- [ ] Experimental setup is fair (same compute, data, hyperparameter budget for baselines)
- [ ] Results are reproducible (seed fixed, enough runs, variance reported)
- [ ] No cherry-picked examples (show distribution, not just best case)
- [ ] Hyperparameters for ALL methods reported (not just yours)

### Completeness
- [ ] Strongest available baselines included
- [ ] Ablation study covers each key component
- [ ] At least one analysis beyond the main result (error analysis, scaling, etc.)
- [ ] Limitations section is honest and non-trivial
- [ ] Broader impact discussed (if applicable)

### Positioning
- [ ] Related work covers all relevant prior work (ask: "what would a reviewer search for?")
- [ ] Contributions are clearly differentiated from prior work
- [ ] Claims match evidence (no overclaiming)
- [ ] Title and abstract accurately represent the paper

### Presentation
- [ ] A non-expert in the subfield can understand the introduction
- [ ] An expert can understand the method in one read
- [ ] Every figure/table is referenced and has a takeaway sentence
- [ ] Paper fits within page limits
- [ ] Supplementary material is organized (not a dump)

## Rebuttal Strategy

### Do
- Thank reviewers for specific points
- Address the top concern first (the one that would change the score)
- Provide NEW evidence: additional experiments, ablations, analysis
- Be specific: "We ran X on Y dataset, achieving Z (see Table R1)"
- Acknowledge valid criticisms: "We agree that X is a limitation"
- Promise concrete revisions: "We will add X to Section Y"

### Don't
- Be defensive or dismissive
- Argue about scores directly ("we deserve a 7")
- Provide vague promises ("we will improve the paper")
- Ignore any weakness (even if you disagree)
- Add excessive new content (focus on what changes the decision)
- Repeat what is already in the paper

### Rebuttal Template

```markdown
We thank the reviewers for their thoughtful feedback. We address the
main concerns below.

**[R1/R2/R3] Concern about X:**
We have conducted [additional experiment/analysis]. The results show
[specific finding], confirming that [conclusion]. We will add this to
Section X in the revision.

**[R2] Missing baseline Y:**
We have now compared against Y. Our method achieves [metric] vs Y's
[metric], a [delta] improvement. See Table R1 below.

| Method | Metric1 | Metric2 |
|--------|---------|---------|
| Y      | ...     | ...     |
| Ours   | ...     | ...     |

**[R3] Clarity of Section Z:**
We agree this section could be clearer. We will [specific revision plan].
```

## Common Fatal Flaws (Instant Reject)

1. **Evaluation on toy data only** — No real-world benchmarks
2. **Missing obvious baselines** — Not comparing to the method everyone knows
3. **Reproducibility impossible** — No details on setup, data, or hyperparameters
4. **Overclaiming** — "State-of-the-art" without actually comparing to SOTA
5. **No ablation** — Cannot tell which component matters
6. **Plagiarism/dual submission** — Ethical violation
7. **Wrong experimental setup** — Data leakage, unfair comparison, train/test contamination
