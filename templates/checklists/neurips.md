# NeurIPS Submission Checklist

> Based on NeurIPS 2025/2026 submission requirements.
> Used by S8_delivery.md for pre-submission verification.

## Mandatory Items

### 1. Paper Checklist (included in submission)
- [ ] **Claims**: Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope?
- [ ] **Limitations**: Does the paper discuss the limitations of the work?
- [ ] **Theory**: For each theoretical result, does the paper include the full set of assumptions and a complete (or correct) proof?
- [ ] **Experiments**: Does the paper include the code, data, and instructions needed to reproduce the main experimental results?
- [ ] **Training details**: Does the paper specify all the training and test details necessary to understand the results?
- [ ] **Error bars**: Does the paper report error bars (e.g., with respect to the random seed)?
- [ ] **Compute**: Does the paper provide sufficient information on compute resources needed to reproduce experiments?

### 2. Broader Impact Statement
- [ ] **Present**: Paper includes a broader societal impact discussion.
- [ ] **Honest**: Negative societal impacts are acknowledged, not just positive ones.
- [ ] **Specific**: Impact discussion is specific to this work, not generic.

### 3. LLM Disclosure (NeurIPS 2025+)
- [ ] **Disclosure present**: If LLMs were used in writing or research, this is disclosed.
- [ ] **Scope clear**: Specifies which parts used LLM assistance.
- [ ] **InfiEpisteme note**: "This paper was produced with the assistance of InfiEpisteme, an automated research pipeline using Claude Code."

### 4. Reproducibility
- [ ] **Code**: Source code is available (or will be upon acceptance).
- [ ] **Data**: Datasets used are publicly available or instructions to obtain them are provided.
- [ ] **Environment**: Computing environment is fully specified (GPU, libraries, versions).
- [ ] **Seeds**: Random seeds are reported.
- [ ] **Hyperparameters**: All hyperparameters are listed (including those from search).
- [ ] **Runs**: Number of runs and statistical significance measures are reported.

### 5. Ethics
- [ ] **IRB**: If human subjects data is used, IRB approval is mentioned.
- [ ] **Consent**: If using crowdsourced data, informed consent is documented.
- [ ] **PII**: Paper does not expose personally identifiable information.
- [ ] **Bias**: Potential biases in data and method are discussed.

### 6. Formatting
- [ ] **Page limit**: Main paper ≤ 10 pages (excluding references and appendix).
- [ ] **Template**: Uses official NeurIPS LaTeX template.
- [ ] **Anonymous**: No author-identifying information in submission version.
- [ ] **Supplementary**: Appendix follows main paper in same PDF.
- [ ] **References**: All references are complete with venue and year.

## Recommended (Not Required)

- [ ] **Ablation study**: Components of the method are individually evaluated.
- [ ] **Comparison**: At least 3 competitive baselines are compared.
- [ ] **Qualitative examples**: Representative examples illustrate method behavior.
- [ ] **Failure cases**: Paper discusses when/where the method fails.
- [ ] **Efficiency**: Computational cost is compared with baselines.
