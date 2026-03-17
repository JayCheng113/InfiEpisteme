# S3 Implementation — Code Development

> Stage 3. Implement baselines, proposed methods, and evaluation harness.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S3`.
2. Read `config.yaml` — compute settings, GPU type.
3. Read `hardware_profile.json` — hardware capabilities. Choose frameworks and training strategies based on available hardware:
   - Single GPU: standard PyTorch training, gradient accumulation if VRAM is limited
   - Multi-GPU: set up DDP/FSDP from the start
   - No GPU: CPU-only or prepare for SSH remote execution
   - VRAM < 16GB: use mixed precision (fp16/bf16), consider gradient checkpointing
4. Read `BASELINES.md` — baseline methods to implement.
5. Read `EXPERIMENT_PLAN.md` — experiment design and evaluation protocol.
6. Read `experiment_tree.json` — root nodes to implement.
7. Read `.ai/core/methodology.md` — proposed approach details.
8. Read `.ai/evolution/negative-results.md` — avoid repeating past mistakes.
9. Read `.ai/evolution/experiment-log.md` — prior experiment context.
10. Check `state/JUDGE_RESULT.json` — if retrying:
   - Read `retry_guidance` for specific code issues.
   - Common failures: node not runnable, baseline mismatch, missing evaluation harness.
   - Fix the specific issues rather than rewriting everything.

### Implementation References
Based on your research task, load the relevant reference guide:
- **Custom small model (< 1B)**: Read `skills/references/impl-nanogpt.md` for nanoGPT patterns
- **Using existing architectures (LLaMA, Mistral)**: Read `skills/references/impl-litgpt.md`
- **Multi-GPU pretraining**: Read `skills/references/impl-torchtitan.md`
- **Distributed training (FSDP)**: Read `skills/references/impl-fsdp2.md`
- **Fast LoRA training**: Read `skills/references/impl-unsloth.md`

### Idempotency Check
- Read `experiment_tree.json` and check node statuses.
- If all root nodes have `status: "runnable"`: verify each actually runs, then skip.
- If some are runnable and others are not: only implement the non-runnable ones.

## Your Role

You are the ML engineer. You write clean, reproducible code for all baselines and proposed methods, create an evaluation harness, and verify everything runs.

## Process

### Step 1: Set Up Project Structure

Ensure this directory structure exists:

```
src/
  method/           # proposed method implementations
    __init__.py
  baselines/        # baseline implementations
    __init__.py
  evaluation/       # evaluation scripts
    __init__.py
    evaluate.py     # main evaluation entry point
  utils/            # shared utilities
    __init__.py
    data.py         # data loading
    metrics.py      # metric computation
    config.py       # configuration management
    seed.py         # reproducibility (seed fixing)
```

### Step 2: Implement Shared Utilities

**`src/utils/seed.py`**: Fix all random seeds (Python, NumPy, PyTorch/JAX).

**`src/utils/data.py`**: Data loading for the target dataset(s). Must handle:
- Train/val/test splits
- Batch iteration
- Data augmentation (if applicable)

**`src/utils/metrics.py`**: Compute the primary and secondary metrics defined in EXPERIMENT_PLAN.md.

**`src/utils/config.py`**: Load experiment configurations from JSON/YAML.

### Step 3: Implement Baselines

For each baseline in BASELINES.md:
1. Create `src/models/{baseline_name}.py`
2. Implement the method following the paper description
3. If open-source code is available (noted in BASELINES.md), reference it
4. Create a run script or entry point
5. Run on a small subset (1% of data or 1 epoch) to verify it executes without errors
6. Compare output format with evaluation harness

### Step 4: Implement Proposed Methods

For each root node in experiment_tree.json:
1. Read the node's `approach` and `key_difference` fields
2. Create `src/models/{node_id}.py` or organize by hypothesis
3. Implement the method as described
4. Ensure it follows the same interface as baselines (same input/output format)
5. Run on a small subset to verify execution
6. Mark node status in experiment_tree.json:
   - `"runnable"` if it executes without errors
   - `"buggy"` if there are unresolved errors (log details)

### Step 5: Create Evaluation Harness

**`src/evaluation/evaluate.py`** must:
- Accept a model/method identifier and config file
- Load the appropriate method
- Run evaluation on the test set
- Compute all metrics (primary + secondary)
- Save results to `results/{node_id}/metrics.json`:
  ```json
  {
    "node_id": "H1_R1",
    "metrics": {
      "primary_metric": value,
      "secondary_metric_1": value
    },
    "config": { ... },
    "timestamp": "...",
    "runtime_seconds": N
  }
  ```
- Generate basic figures (learning curves, metric plots)

### Step 6: Verify Baselines Against Reported Numbers

Run each baseline through the full evaluation pipeline (not just smoke test):
1. Train baseline on the full dataset (or as much as budget allows)
2. Evaluate and compare with numbers in BASELINES.md
3. Acceptable tolerance: +/- 5% of reported numbers
4. If outside tolerance:
   - Debug the implementation
   - Check data preprocessing differences
   - Document the discrepancy and your analysis
   - Log to `.ai/evolution/negative-results.md` if truly unresolvable

### Step 7: Update Requirements

Ensure `requirements.txt` includes all ML dependencies:
- Framework (torch, tensorflow, jax, etc.)
- Data processing libraries
- Evaluation libraries
- Visualization (matplotlib, seaborn)
- Pin major versions for reproducibility

### Step 8: Write README_code.md

```markdown
# Code Documentation

## Setup
pip install -r requirements.txt

## Running Baselines
python src/models/{name}.py --config configs/{name}.yaml

## Running Proposed Methods
python src/models/{name}.py --config configs/{node_id}.yaml

## Evaluation
python src/evaluation/evaluate.py --method {name} --config configs/{name}.yaml

## Reproducing All Experiments
./run_all.sh  # or python run_experiments.py
```

### Step 9: Update experiment_tree.json

For each root node, update:
```json
{
  "status": "runnable" | "buggy",
  "code_path": "src/models/{file}.py",
  "config_path": "configs/{node_id}.yaml",
  "verified": true | false,
  "verification_notes": "runs without errors on small test"
}
```

## Output

| File | Action |
|------|--------|
| `src/models/` | Create method and baseline implementations |
| `src/evaluation/` | Create evaluation harness |
| `src/utils/` | Create shared utilities |
| `requirements.txt` | Update with ML dependencies |
| `README_code.md` | Create reproduction instructions |
| `experiment_tree.json` | Update node statuses |

## .ai/ Updates

| File | Action |
|------|--------|
| `.ai/evolution/experiment-log.md` | Log baseline verification runs |
| `.ai/evolution/negative-results.md` | Log any baseline discrepancies or buggy nodes |

## Quality Criteria (from PIPELINE.md)

- [ ] All root nodes in experiment_tree.json have status=runnable
- [ ] Baselines implemented and verified against reported numbers (+/-5%)
- [ ] Evaluation harness runs without errors on test data
- [ ] README_code.md has reproduction instructions

## Rules

- Write clean, documented code with docstrings.
- Use seed-based reproducibility — fix all random seeds via `src/utils/seed.py`.
- Never hardcode file paths — use config files or argparse.
- Log all training runs with configs and results.
- Save checkpoints for long-running experiments.
- Keep baseline implementations faithful to the original papers.
- If a node is buggy, document exactly what fails and why.
- Do not run full experiments — that is S4's job. Only verify code runs.

## When Done

- All `src/` code is implemented and organized.
- All root nodes are `runnable` (or documented as `buggy` with reasons).
- Baselines are verified against reported numbers.
- `README_code.md` provides clear reproduction instructions.
- Commit: `S3: implement {N} baselines and {M} method variants`
- Commit: `docs(.ai): log baseline verification results`
