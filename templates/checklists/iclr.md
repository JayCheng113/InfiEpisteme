# ICLR Submission Checklist

> Based on ICLR 2026 submission requirements.
> Used by S8_delivery.md for pre-submission verification.

## Mandatory Items

### 1. LLM Usage Statement (**Missing = Desk Rejection**)
- [ ] **CRITICAL**: Paper includes a clear statement about LLM usage in research and writing.
- [ ] **Scope**: Specifies which aspects (writing, coding, analysis) used LLM assistance.
- [ ] **InfiEpisteme disclosure**: "Research conducted with InfiEpisteme automated pipeline (Claude Code)."
- [ ] **Human oversight**: Describes how results were verified by humans.

> **WARNING**: ICLR 2025+ requires explicit LLM usage disclosure. Papers missing this statement may be desk-rejected without review.

### 2. Reproducibility
- [ ] **Code**: Code is available or will be released.
- [ ] **Data**: All datasets are accessible or creation process is documented.
- [ ] **Environment**: Full environment specification (hardware, software, versions).
- [ ] **Seeds**: All random seeds reported.
- [ ] **Hyperparameters**: Complete hyperparameter specification with search strategy.
- [ ] **Training details**: Epochs, batch size, optimizer, learning rate schedule.
- [ ] **Compute budget**: Total compute used (GPU hours, hardware type).

### 3. Evaluation Standards
- [ ] **Metrics**: All metrics are clearly defined.
- [ ] **Statistical significance**: Reported with appropriate tests.
- [ ] **Multiple runs**: Results averaged over multiple seeds.
- [ ] **Fair comparison**: Same computational budget for baselines.
- [ ] **Standard benchmarks**: Evaluation on recognized benchmarks where possible.

### 4. Ethics
- [ ] **Impact**: Discussion of broader implications.
- [ ] **Limitations**: Honest discussion of method limitations.
- [ ] **Biases**: Potential biases in data and approach.

### 5. Formatting
- [ ] **Page limit**: Main paper ≤ 10 pages (excluding references and appendix).
- [ ] **Template**: Official ICLR LaTeX template.
- [ ] **Anonymous**: Double-blind submission.
- [ ] **PDF size**: Under 50MB.
- [ ] **References**: Complete with URLs where available.

## Recommended

- [ ] **Ablation study**: Component-wise analysis.
- [ ] **Efficiency comparison**: FLOPs, latency, memory vs baselines.
- [ ] **Qualitative analysis**: Example outputs or visualizations.
- [ ] **Failure analysis**: When does the method fail?
- [ ] **Theoretical justification**: Why the method should work.
