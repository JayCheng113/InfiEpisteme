# Generic ML Paper Checklist

> For arXiv submissions or when no specific venue is targeted.
> Used by S8_delivery.md for pre-submission verification.

## Core Quality Checks

### 1. Claims and Evidence
- [ ] **Claims match evidence**: Every claim in abstract/introduction is supported by experimental results.
- [ ] **No overclaiming**: Language accurately reflects the magnitude of improvements.
- [ ] **Limitations discussed**: Paper honestly addresses what the method cannot do.

### 2. Reproducibility
- [ ] **Code available**: Source code is provided or will be released.
- [ ] **Data accessible**: All datasets are publicly available or creation is documented.
- [ ] **Environment specified**: Hardware, software versions, dependencies listed.
- [ ] **Seeds reported**: All random seeds documented.
- [ ] **Hyperparameters complete**: Every hyperparameter value is specified.
- [ ] **Training details**: Optimizer, learning rate, batch size, epochs, etc.
- [ ] **Compute budget**: Total GPU hours and hardware type reported.

### 3. Experimental Rigor
- [ ] **Multiple runs**: Results averaged over ≥ 3 random seeds.
- [ ] **Error bars**: Standard deviation or confidence intervals reported.
- [ ] **Statistical tests**: Significance tests for main comparisons.
- [ ] **Fair baselines**: Baselines given comparable tuning effort.
- [ ] **Ablation study**: Key components individually evaluated.
- [ ] **Negative results**: Failed approaches documented (at least mentioned).

### 4. Citation Quality
- [ ] **All citations verified**: Every reference confirmed via Semantic Scholar or DOI.
- [ ] **No phantom citations**: Every \cite{} has a bibliography.bib entry.
- [ ] **No fabricated papers**: Every paper in bibliography is real and findable.
- [ ] **Proper attribution**: Original work cited, not just surveys.
- [ ] **Recent work included**: Literature survey covers last 2 years.

### 5. Writing Quality
- [ ] **Clear structure**: Standard sections (Intro, Related Work, Method, Experiments, Conclusion).
- [ ] **Consistent notation**: Mathematical notation defined on first use and consistent throughout.
- [ ] **Figures informative**: Every figure has a clear caption and supports a specific point.
- [ ] **Tables readable**: Proper formatting (booktabs), clear headers, units specified.
- [ ] **No redundancy**: Information not repeated across sections unnecessarily.

### 6. LLM Disclosure
- [ ] **Disclosed**: If LLMs assisted in writing or research, this is stated.
- [ ] **InfiEpisteme note**: Automated pipeline usage disclosed.

### 7. Ethics and Impact
- [ ] **Broader impact**: Potential societal implications discussed.
- [ ] **Data ethics**: Data collection and usage is ethical.
- [ ] **Bias awareness**: Known biases in data/method acknowledged.

## Paper-Result Consistency

- [ ] **Numbers match**: Every number in tables/text matches `results/*/metrics.json`.
- [ ] **Figures match**: Every figure in paper corresponds to actual experiment output.
- [ ] **No selective reporting**: All experiments in the plan are reported (including negative).

## Final Checks

- [ ] **PDF compiles**: LaTeX compiles without errors or warnings.
- [ ] **No undefined references**: No "??" in the compiled PDF.
- [ ] **Page count appropriate**: Within typical range for the format.
- [ ] **Bibliography complete**: No missing fields in BibTeX entries.
- [ ] **Spell check**: No obvious typos (especially in abstract and introduction).
