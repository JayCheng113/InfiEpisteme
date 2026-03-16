# ICML Submission Checklist

> Based on ICML 2025/2026 submission requirements.
> Used by S8_delivery.md for pre-submission verification.

## Mandatory Items

### 1. Reproducibility Checklist
- [ ] **Assumptions**: All assumptions are clearly stated.
- [ ] **Proofs**: Complete proofs of all theoretical results are included in supplementary if not in main paper.
- [ ] **Experimental setup**: Complete description of experimental setup and evaluation.
- [ ] **Hyperparameters**: How hyperparameters were selected (grid search, random search, etc.) is described.
- [ ] **Best hyperparameters**: Final hyperparameter values are reported.
- [ ] **Runs**: Number of runs and seeds are specified.
- [ ] **Error bars**: Mean ± std or confidence intervals are reported.
- [ ] **Statistical tests**: Appropriate statistical tests are used for comparing methods.
- [ ] **Datasets**: Exact dataset versions and splits are specified.
- [ ] **Data preprocessing**: All preprocessing steps are documented.
- [ ] **Code**: Code will be released or is submitted as supplementary.

### 2. Statistical Reporting Standards
- [ ] **Significance**: P-values or confidence intervals for main claims.
- [ ] **Multiple comparisons**: Correction for multiple hypothesis testing if applicable (Bonferroni, etc.).
- [ ] **Effect sizes**: Not just p-values but magnitude of improvement.
- [ ] **Baseline fairness**: Baselines are run with same compute budget / tuning effort.

### 3. Ethics and Impact
- [ ] **Societal impact**: Discussion of potential societal consequences.
- [ ] **Dual use**: If applicable, discussion of potential misuse.
- [ ] **Privacy**: Data handling respects privacy requirements.

### 4. LLM Usage Disclosure
- [ ] **Disclosed**: Any use of LLMs in research or writing is declared.
- [ ] **InfiEpisteme note**: Pipeline-assisted research is disclosed.

### 5. Formatting
- [ ] **Page limit**: Main paper ≤ 10 pages (excluding references and appendix).
- [ ] **Template**: Uses official ICML LaTeX template.
- [ ] **Anonymous**: Double-blind — no author-identifying information.
- [ ] **Supplementary**: Appendix and code in supplementary materials.
- [ ] **References**: Complete bibliographic entries.

## Recommended

- [ ] **Computational cost**: Wall-clock time and hardware used.
- [ ] **Memory usage**: Peak memory requirements reported.
- [ ] **Scaling analysis**: How method scales with data/model size.
- [ ] **Ablation study**: Contribution of each component.
- [ ] **Negative results**: Approaches that did not work.
