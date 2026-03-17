# ML Paper Writing Guide
> Reference for S6/S7. Load when writing or revising the research paper.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## The Narrative Principle: What / Why / So What

Every section, paragraph, and sentence should answer one of:
- **What** — What did you do? What did you find?
- **Why** — Why does this matter? Why this approach?
- **So What** — What are the implications? What should readers do with this?

## 5-Sentence Abstract Formula

```
1. [Context] — Establish the problem area and its importance.
2. [Gap] — What is missing or broken in current approaches.
3. [Approach] — What you did (1 sentence, be specific).
4. [Results] — Key quantitative results (numbers!).
5. [Implication] — Why this matters going forward.
```

Example:
> Large language models struggle with multi-step mathematical reasoning.
> Existing methods rely on supervised fine-tuning, which requires expensive
> step-level annotations. We introduce Group Relative Policy Optimization
> (GRPO), which improves reasoning through reward-based RL without human
> annotations. GRPO achieves 72.3% on GSM8K (+8.1% over SFT baseline)
> using only outcome-level rewards. This demonstrates that process
> supervision can emerge from outcome-based training alone.

## Gopen & Swan: 7 Principles of Clear Scientific Writing

| # | Principle | Practical Rule |
|---|-----------|---------------|
| 1 | **Stress position** | Put the most important info at the end of a sentence |
| 2 | **Topic position** | Start each sentence with familiar/old information |
| 3 | **One point per paragraph** | Each paragraph has one main point, stated in the first sentence |
| 4 | **Context before action** | Set up "why" before "what" |
| 5 | **Subject-verb proximity** | Keep subject and verb close together |
| 6 | **Consistent terms** | Use the same word for the same concept throughout |
| 7 | **Logical flow** | Each sentence connects to the next via old-to-new information |

## Word Choice: Vague to Specific

| Avoid | Use Instead |
|-------|-------------|
| "good results" | "achieves 85.3% accuracy (+4.2% over baseline)" |
| "significantly better" | "statistically significant (p < 0.01, paired t-test)" |
| "we believe" | "the results suggest" or "we hypothesize" |
| "a lot of" | "47 out of 57 tasks" |
| "recently" | "since 2023" or "following [Author, 2024]" |
| "state-of-the-art" | "outperforms [best published method] by X%" |
| "novel" | describe what is actually new |
| "simple" | "requires only X, without Y" |
| "interesting" | explain WHY it is interesting |
| "obviously" | remove entirely, or prove it |
| "we use" | "we apply/employ/adopt" (vary appropriately) |
| "big model" | "7B-parameter model" |

## Time Allocation

Spend roughly equal time on each:
1. **Abstract** (~25%) — Most-read part. Every word counts.
2. **Introduction** (~25%) — Sells the paper. Must be compelling.
3. **Figures and Tables** (~25%) — Reviewers scan these first.
4. **Everything else** (~25%) — Method, experiments, related work, conclusion.

## Section-by-Section Guide

### Introduction (1-1.5 pages)

```
Paragraph 1: Why this problem matters (broad context)
Paragraph 2: What current methods do and why they fall short
Paragraph 3: Your key insight / approach (1-2 sentences)
Paragraph 4: What you did and what you found (preview of results)
Paragraph 5: Contributions list (3-4 bullet points)
```

### Related Work (0.75-1 page)

- Group by theme, not chronologically
- Each group: "X does A, Y does B, but none do C (which we address)"
- End each paragraph by differentiating your work
- Be generous: cite relevant work, don't dismiss competitors

### Method (1.5-2.5 pages)

- Start with problem formulation (notation)
- Build up from simple to complex
- One figure showing the method overview
- Use consistent notation throughout
- Every design choice needs justification ("We use X because Y")

### Experiments (2-3 pages)

- Start with experimental setup (datasets, baselines, metrics, hyperparameters)
- Main results table first, then ablations
- Every table/figure must have a takeaway sentence
- Report confidence intervals or standard deviations
- Ablation study: remove one component at a time

### Conclusion (0.5 page)

- Restate main finding (not just repeat abstract)
- Limitations (shows maturity, reviewers respect honesty)
- Future work (1-2 concrete directions)

## Figure Best Practices

- Every figure must be readable in grayscale
- Font size in figures >= caption font size
- Axis labels with units
- Legend inside the plot (not separate)
- Error bars or shaded confidence regions
- Caption should be self-contained (reader understands without reading text)

## Reviewer Scoring Rubric (NeurIPS Scale)

| Score | Meaning | What Triggers It |
|-------|---------|-----------------|
| 1-3 | Reject | Wrong, incomplete, or trivial |
| 4 | Borderline reject | Incremental, weak experiments, unclear writing |
| 5 | Borderline accept | Solid but not exciting, minor issues |
| 6 | Accept | Clear contribution, good experiments, well-written |
| 7 | Strong accept | Novel + thorough + well-written |
| 8-10 | Top paper | Transformative contribution |

**To get a 6+:**
- Clear, specific contributions
- Strong baselines (not just weak ones)
- Ablations proving each component matters
- Error analysis (where does it fail?)
- Honest limitations section

## Pre-Submission Checklist

### Content
- [ ] Abstract follows the 5-sentence formula
- [ ] Introduction ends with numbered contributions
- [ ] Every claim has evidence (number, citation, or proof)
- [ ] All baselines are recent and strong
- [ ] Ablation study covers all key components
- [ ] Limitations section is honest and specific

### Formatting
- [ ] Page limit respected (excluding references)
- [ ] All figures/tables referenced in text
- [ ] Consistent notation throughout
- [ ] No orphan sections (section with only one subsection)
- [ ] References formatted correctly (no "[?]" markers)
- [ ] Anonymous (no identifying information in blind review)

### Figures and Tables
- [ ] All figures readable at print size
- [ ] All tables have captions above, figures have captions below
- [ ] Numbers aligned on decimal point in tables
- [ ] Best results bolded in comparison tables
- [ ] Color scheme is colorblind-friendly

### Writing Quality
- [ ] No first-person opinions without evidence ("we believe")
- [ ] No vague quantifiers ("significantly", "much better")
- [ ] Consistent terminology (same word = same concept)
- [ ] Spell-checked, grammar-checked
- [ ] Read aloud for flow

## Common Reviewer Complaints (Avoid These)

1. "The contribution is incremental" → Be explicit about what is NEW
2. "Missing baselines" → Include the strongest recent method
3. "No ablation study" → Show each component's contribution
4. "The paper is hard to follow" → Get someone else to read it
5. "Overclaims" → Match claims to evidence precisely
6. "No error analysis" → Show failure cases
7. "Reproducibility concerns" → Include all hyperparameters, promise code release
