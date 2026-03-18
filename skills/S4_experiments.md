# S4 Experiments — Progressive Tree Search Orchestration

> Stage 4. Orchestrates the 4-stage experiment tree search.
> Inherits: `_common.md`
> Sub-skill: `S4_run_node.md` for individual node execution.

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S4`. Note `tree_stages_complete`.
2. Read `config.yaml` — get GPU budget, parallel_jobs, gpu_type, MCP settings.
3. Read `hardware_profile.json` — hardware capabilities. Use `recommendations.parallel_experiments` for max concurrent jobs. Adjust batch sizes per `recommendations.max_batch_size_estimate`.
4. Read `experiment_tree.json` — current tree state and node statuses.
5. Read `EXPERIMENT_PLAN.md` — evaluation protocol, primary metric.
6. Read `.ai/core/methodology.md` — approach details.
7. Read `.ai/evolution/negative-results.md` — avoid repeating failed approaches.
8. Read `.ai/evolution/experiment-log.md` — prior runs.
9. Check `state/JUDGE_RESULT.json` — if retrying:
   - Read `retry_guidance` to see which tree stage failed.
   - Resume from the failed tree stage, not from the beginning.

### Training Framework References
Based on experiment type, load the relevant guide:
- **Standard pretraining**: Read `skills/references/impl-nanogpt.md` or `skills/references/impl-litgpt.md`
- **RL/alignment training (GRPO, PPO, DPO)**: Read `skills/references/impl-trl-grpo.md` or `skills/references/impl-trl.md`
- **Multi-GPU distributed**: Read `skills/references/impl-fsdp2.md` or `skills/references/impl-torchtitan.md`
- **Memory-constrained single GPU**: Read `skills/references/impl-unsloth.md`

### Idempotency Check
- Check `tree_stages_complete` in registry.yaml.
- If a tree stage is already complete (all nodes have results), skip it.
- If partially complete, resume from the first incomplete node.
- Check `results/{node_id}/metrics.json` existence for each node.

### Budget Check (MANDATORY — do this BEFORE any training)
Before ANY experiment submission, calculate actual GPU hours:

1. Read `hardware_profile.json` → get GPU throughput (approximate: A100-40GB ≈ 50K tokens/s for 0.5B model with bf16)
2. For each node, calculate: `hours = total_tokens / tokens_per_sec / 3600`
3. Sum all planned nodes for this sub-stage
4. Compare against remaining budget from `config.yaml compute.gpu_hours`

```
Example: 6 nodes × 500M tokens each, 50K tokens/s
= 6 × (500M / 50K / 3600) = 6 × 2.78 = 16.7 GPU-hours
```

**If total exceeds budget**: reduce tokens per node (S4.1: 100-200M is enough for preliminary validation), drop lower-priority nodes, or flag for human decision. Do NOT proceed and silently exceed budget.

## Your Role

You orchestrate the progressive tree search across 4 stages. You dispatch individual node executions (via S4_run_node logic), collect results, select winners, and expand the tree.

## Process

### Step 0: Determine What This Experiment Tree Search Needs

Before following the default sub-stage templates below, read `EXPERIMENT_PLAN.md` and `experiment_tree.json`. The phase plan in EXPERIMENT_PLAN.md defines what each sub-stage should actually do for THIS specific research. The templates below (4.1-4.4) are defaults — override them when the phase plan specifies something different.

Answer these questions:
1. **What does the phase plan say each sub-stage should do?** If EXPERIMENT_PLAN.md defines Phase 4.2 as "cross-architecture validation on Pythia," do that — not the default "hyperparameter tuning."
2. **Which sub-stages depend on previous results?** If Phase 4.3's design says "choose architecture based on 4.2 results," then after 4.2 completes, analyze the results and decide before proceeding. Do not follow a pre-determined plan blindly.
3. **Does the budget still support the plan?** Recalculate after each sub-stage based on actual (not estimated) GPU hours consumed.

Write your Step 0 analysis as a brief note at the top of `RESULTS_SUMMARY.md` before starting 4.1.

**Decision points between sub-stages**: After each sub-stage completes, before starting the next:
- Read the phase plan for the next sub-stage
- If the plan says "decide based on results," analyze the results and record your decision in `.ai/evolution/decisions.md`
- If the plan specifies a fixed design, follow it
- If budget is insufficient for the planned next sub-stage, propose a reduced scope and note the trade-off

**State consistency check between sub-stages** (REQUIRED):
- Verify `winner` fields in experiment_tree.json match the methods that ACTUALLY advance to the next sub-stage per EXPERIMENT_PLAN.md. If the plan was revised (e.g., methods dropped/replaced), winners may be stale. Fix before creating child nodes.
- Verify `hardware_profile.json` → `recommendations.throughput_reference` reflects measured throughput from the COMPLETED sub-stage (not estimates from initial hardware detection). Stale throughput data causes wrong budget calculations.
- Verify the training script's invocation command works: `python -m src.train --help` (or equivalent). If the script uses package imports, `python3 src/train.py` will fail with ImportError.

### Stage 4.1: Preliminary Investigation

**Goal**: Run all root nodes with SHORT training to quickly validate which approaches work.

**Token budget for S4.1**: Use 100-200M tokens per node (NOT the full training budget). This is a preliminary screening — you need enough signal to compare methods, not converged models. At 50K tokens/s, 200M tokens ≈ 1.1 hours per node. Full training happens in S4.2-S4.3 for winners only.

1. **Collect runnable root nodes** from experiment_tree.json (status=runnable).
2. **Git Pre-Registration** (before ANY experiment execution):
   ```bash
   git add experiment_tree.json EXPERIMENT_PLAN.md
   git commit -m "research(protocol): {hypothesis} — {approach_summary}"
   ```
   This proves the experimental design was committed before observing results.

3. **For each root node**, execute the experiment:

   **Via SSH MCP** (if `config.yaml` has `mcp.ssh_remote: true`):
   - Use `mcp__ssh__execute_command` to submit: `nohup python3 src/train.py --config configs/{id}.yaml > results/{id}/logs/train.log 2>&1 &`
   - Poll via `mcp__ssh__execute_command`: `cat results/{id}/metrics.json 2>/dev/null`

   **Via Python scripts** (fallback):
   - Submit GPU job: `python3 scripts/gpu_submit.py --node {id} --script src/train.py --config configs/{id}.yaml`
   - Poll for completion: `python3 scripts/gpu_poll.py --node {id}`

   - If poll returns success: read `results/{node_id}/metrics.json`
   - If poll returns failure: mark node as `buggy`, log to negative-results.md
4. **For each completed node**:
   - Generate figures: run the figure generation code
   - Submit figures for VLM review (invoke VLM review logic)
   - If VLM score < 4: regenerate with feedback (max 3 attempts)
4. **Classify nodes**:
   - `buggy`: errors, NaN results, unreasonable values
   - `non-buggy`: plausible results, within expected range
5. **Select best non-buggy node per hypothesis** based on primary metric.
6. Update experiment_tree.json: set `winner: true` on selected nodes.
7. **Git Result Commit** (after each batch completes):
   ```bash
   git add results/ experiment_tree.json
   git commit -m "research(results): stage_4.1 — best={best_node_id}, {metric}={value}"
   ```
8. Update registry.yaml: `tree_stages_complete: 1`.

**Failure handling**: If ALL root nodes for a hypothesis are buggy:
- Log to negative-results.md with details.
- Check if the approach is fundamentally flawed.
- Consider: can we generate 1-2 new root nodes with simpler variants?
- If no viable path: mark hypothesis as failed, continue with remaining hypothesis.

### Stage 4.2: Extended Evaluation

**Default goal**: Fine-tune the best variants from Stage 4.1. **But check EXPERIMENT_PLAN.md first** — the phase plan may specify something different (e.g., cross-architecture validation, longer training, additional baselines).

**Default template** (use only if phase plan does not specify otherwise):
For each Stage 4.1 winner:
1. Create **3 child nodes** varying one hyperparameter each:
   - Child 1: vary learning rate (e.g., 0.5x and 2x)
   - Child 2: vary model size or capacity
   - Child 3: vary regularization or training duration
2. Add children to experiment_tree.json with `stage: "4.2"`, `parent: {winner_id}`.
3. Execute all children (same submit/poll/review cycle as Stage 4.1).
4. Select best child per hypothesis.
5. Update experiment_tree.json and registry.yaml: `tree_stages_complete: 2`.

### Stage 4.3: Full-Scale Validation

**Default goal**: Improve the method itself. **But check EXPERIMENT_PLAN.md first** — the phase plan often specifies full-scale training, cross-architecture validation, or other designs that override this default.

**If the phase plan says "decide based on 4.2 results"**: Analyze 4.2 results BEFORE designing 4.3 nodes. Specifically:
- Compare method rankings across conditions tested in 4.2 (architectures, scales, etc.)
- If rankings are consistent → proceed with the primary architecture/scale
- If rankings diverge → investigate the divergence (run the surprising condition at full scale)
- Record your analysis and decision in `.ai/evolution/decisions.md` as an ADR

**Default template** (use only if phase plan does not specify otherwise):
For each Stage 4.2 winner:
1. Analyze results — what is the error pattern? Where does the method struggle?
2. Create **3 child nodes** with method-level improvements:
   - Child 1: architectural change (e.g., different attention, different loss)
   - Child 2: training strategy change (e.g., curriculum learning, data augmentation)
   - Child 3: ensemble or combination approach
3. Execute, evaluate, select best.
4. Update tree and registry: `tree_stages_complete: 3`.

### Stage 4.4: Ablation Studies

**Goal**: Understand component contributions.

For each Stage 4.3 winner:
1. Identify key components of the winning method.
2. Create **ablation nodes** — each removes one component:
   - `{winner}_no_{component_A}`
   - `{winner}_no_{component_B}`
   - `{winner}_no_{component_C}`
   - `{winner}_baseline_config` (simplest viable config)
3. Execute all ablation nodes.
4. Collect ablation table: Full model vs. each ablation variant.
5. Update tree and registry: `tree_stages_complete: 4`.

## VLM Figure Gate

After every figure generation:
1. Submit figure to VLM review (see `vlm_review.md` skill).
2. Score >= 4/5: figure approved.
3. Score < 4/5: regenerate with VLM-provided feedback.
4. Maximum 3 regeneration attempts per figure.
5. If still failing after 3 attempts: keep best version, flag for human review.

## Experiment Logging

After EVERY node execution, log results in your stage output files (e.g., `RESULTS_SUMMARY.md`, `experiment_tree.json`). The Memory Synthesizer (`memory_sync.md`) will consolidate these into `.ai/evolution/experiment-log.md` and `.ai/evolution/negative-results.md` after your skill completes.

Exception: If you discover a critical failure during your work, you MAY append to `.ai/evolution/negative-results.md` immediately (per `_common.md` rules).

## Output Files

### Per Node
```
results/{node_id}/
  metrics.json      # evaluation metrics
  config.json       # experiment configuration
  figures/           # generated figures
  logs/              # training logs
```

### RESULTS_SUMMARY.md

Use template from `templates/RESULTS_SUMMARY.md`:

```markdown
# Results Summary

## Best Method
- **Node ID**: {winning node from 4.3}
- **Approach**: {description}
- **Configuration**: {key hyperparameters}

## Main Results
| Method | {Metric 1} | {Metric 2} | {Metric 3} |
|--------|-----------|-----------|-----------|
| Baseline 1 | ... | ... | ... |
| Baseline 2 | ... | ... | ... |
| **Ours** | ... | ... | ... |

## Ablation Results
| Variant | {Metric} | Delta from Full |
|---------|---------|----------------|
| Full model | ... | -- |
| - Component A | ... | ... |

## Key Figures
- figures/{name}.png — {description}

## Winning Path Through Tree
{node} (4.1) -> {node} (4.2) -> {node} (4.3) -> ablations (4.4)
```

### experiment_tree.json
Fully populated with all nodes, results, winners, and the complete tree path.

## .ai/ Updates

| File | Action |
|------|--------|
| `.ai/evolution/experiment-log.md` | Append entries for every node run |
| `.ai/evolution/negative-results.md` | Append entries for every failure |

## Quality Criteria (from PIPELINE.md)

- [ ] Stage 4.4 (ablation studies) complete
- [ ] >= 1 method outperforms all baselines on primary metric
- [ ] All figures VLM-approved (score >= 4/5)
- [ ] Negative results documented

## Safety Rules

- **Budget enforcement**: Check remaining GPU budget before EVERY batch submission.
- **Circuit breaker**: If 3 consecutive nodes fail with the same error, pause and diagnose.
- **No silent failures**: Every error must be logged.
- **Checkpoint policy**: For experiments > 1 hour, require checkpointing.
- **Parallel limit**: Do not exceed `config.compute.parallel_jobs` concurrent jobs.

## When Done

- `RESULTS_SUMMARY.md` exists with main results and ablations.
- `experiment_tree.json` is fully populated through Stage 4.4.
- All figures are VLM-approved.
- All experiments are logged.
- `registry.yaml` has `tree_stages_complete: 4`.
- Commit: `S4: tree search complete — best method achieves {metric}: {value}`
- Commit: `docs(.ai): log all experiment results and negative findings`
