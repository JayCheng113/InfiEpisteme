# S4 Experiments — Progressive Tree Search Orchestration

> Stage 4. Orchestrates the 4-stage experiment tree search.
> Inherits: `_common.md`
> Sub-skill: `S4_run_node.md` for individual node execution.

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S4`. Note `tree_stages_complete`.
2. Read `config.yaml` — get GPU budget, parallel_jobs, gpu_type.
3. Read `experiment_tree.json` — current tree state and node statuses.
4. Read `EXPERIMENT_PLAN.md` — evaluation protocol, primary metric.
5. Read `.ai/core/methodology.md` — approach details.
6. Read `.ai/evolution/negative-results.md` — avoid repeating failed approaches.
7. Read `.ai/evolution/experiment-log.md` — prior runs.
8. Check `state/JUDGE_RESULT.json` — if retrying:
   - Read `retry_guidance` to see which tree stage failed.
   - Resume from the failed tree stage, not from the beginning.

### Idempotency Check
- Check `tree_stages_complete` in registry.yaml.
- If a tree stage is already complete (all nodes have results), skip it.
- If partially complete, resume from the first incomplete node.
- Check `results/{node_id}/metrics.json` existence for each node.

### Budget Check
Before ANY experiment submission:
```python
# Estimate GPU hours for this batch
estimated_hours = num_nodes * estimated_hours_per_node
remaining_budget = config.compute.gpu_hours - total_hours_used
if estimated_hours > remaining_budget:
    STOP and report: "Insufficient GPU budget. Need {estimated} hours, have {remaining}."
```

## Your Role

You orchestrate the progressive tree search across 4 stages. You dispatch individual node executions (via S4_run_node logic), collect results, select winners, and expand the tree.

## Process

### Stage 4.1: Preliminary Investigation

**Goal**: Run all root nodes, classify as buggy/non-buggy, select best per hypothesis.

1. **Collect runnable root nodes** from experiment_tree.json (status=runnable).
2. **For each root node**, execute the experiment:
   - Submit GPU job: `python3 scripts/gpu_submit.py --node {id} --script src/method/train.py --config configs/{id}.yaml`
   - Poll for completion: `python3 scripts/gpu_poll.py --node {id}`
   - If poll returns success: read `results/{node_id}/metrics.json`
   - If poll returns failure: mark node as `buggy`, log to negative-results.md
3. **For each completed node**:
   - Generate figures: run the figure generation code
   - Submit figures for VLM review (invoke VLM review logic)
   - If VLM score < 4: regenerate with feedback (max 3 attempts)
4. **Classify nodes**:
   - `buggy`: errors, NaN results, unreasonable values
   - `non-buggy`: plausible results, within expected range
5. **Select best non-buggy node per hypothesis** based on primary metric.
6. Update experiment_tree.json: set `winner: true` on selected nodes.
7. Update registry.yaml: `tree_stages_complete: 1`.

**Failure handling**: If ALL root nodes for a hypothesis are buggy:
- Log to negative-results.md with details.
- Check if the approach is fundamentally flawed.
- Consider: can we generate 1-2 new root nodes with simpler variants?
- If no viable path: mark hypothesis as failed, continue with remaining hypothesis.

### Stage 4.2: Hyperparameter Tuning

**Goal**: Fine-tune the best variant from Stage 4.1.

For each Stage 4.1 winner:
1. Create **3 child nodes** varying one hyperparameter each:
   - Child 1: vary learning rate (e.g., 0.5x and 2x)
   - Child 2: vary model size or capacity
   - Child 3: vary regularization or training duration
2. Add children to experiment_tree.json with `stage: "4.2"`, `parent: {winner_id}`.
3. Execute all children (same submit/poll/review cycle as Stage 4.1).
4. Select best child per hypothesis.
5. Update experiment_tree.json and registry.yaml: `tree_stages_complete: 2`.

### Stage 4.3: Method Refinement

**Goal**: Improve the method itself, not just hyperparameters.

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

After EVERY node execution, append to `.ai/evolution/experiment-log.md`:

```
| {date} | {node_id} | {description} | {primary_metric: value} | {notes} |
```

After EVERY failure, append to `.ai/evolution/negative-results.md`:
- What was tried
- What happened (error message, unexpected result)
- Why it likely failed
- Implications for future attempts

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
