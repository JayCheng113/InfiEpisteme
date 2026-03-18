# Human Checkpoint: S2 — Experimental Design

> Fixed checklist. After this point, GPU hours start being spent.
> This is the "measure twice, cut once" gate.

## Layer A: Fixed Checklist (human-designed)

- [ ] **One node = one variable**: Open `experiment_tree.json`. Does each node correspond to exactly one training run testing one thing? Nodes that pack multiple training runs break budget tracking and make results hard to interpret.
- [ ] **Architecture coverage**: How many architectures are being tested? For a benchmark claim at a top venue, you typically need ≥2 (e.g., LLaMA + Pythia). Check if this is planned.
- [ ] **Budget arithmetic**: Count the nodes. Multiply by estimated hours per node (check `hardware_profile.json` for throughput). Compare with `config.yaml compute.gpu_hours`. Is there room for S4.2-S4.4 (tuning, refinement, ablations) after S4.1?
- [ ] **Evidence basis**: Check each hypothesis in `EXPERIMENT_PLAN.md`. Are speculative claims labeled as such? Are any assertions presented as fact without citation?
- [ ] **Baseline adequacy**: Are the baselines the ones a reviewer would expect? Are any important competing methods missing?
- [ ] **Metric appropriateness**: Is the primary metric (e.g., perplexity, accuracy) the right one for the research question? Are there secondary metrics that matter?

## Layer B: LLM Adversarial Brief

> Auto-generated below by the judge. These are the weakest points identified by the LLM.

{LLM_BRIEF}

## Layer C: Raw Files

- `EXPERIMENT_PLAN.md` — full experiment design
- `experiment_tree.json` — all nodes with configurations
- `hardware_profile.json` — hardware capabilities
- `config.yaml` — compute budget and settings

## Response

Approve: `./run.sh approve`
Approve with changes: `./run.sh approve --with "your modifications here"`
