# S4 Run Node — Execute a Single Experiment Node

> Sub-skill of S4_experiments. Executes one experiment node end-to-end.
> Inherits: `_common.md`

## Before You Start

1. Read `experiment_tree.json` — find the specific node to execute.
2. Read `config.yaml` — GPU settings, budget, and MCP settings.
3. Read `hardware_profile.json` — use `recommendations.max_batch_size_estimate` to set appropriate batch sizes. Adjust config if node's batch size exceeds VRAM capacity.
4. Read `.ai/evolution/negative-results.md` — check if this node or a similar one has failed before.
5. Check `results/{node_id}/metrics.json` — if it already exists with valid results, skip execution.
6. Verify the node has `status: "runnable"`. If `status: "buggy"`, attempt to fix first.

## Input

This skill receives a `node_id` parameter identifying which node to execute. The node's full configuration is in experiment_tree.json.

## Process

### Step 0.5: Check GPU Availability

Before starting any training, verify the GPU is not already occupied by other processes:
```bash
nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv,noheader
```
- If other training processes are running: **STOP**. Report what is running and ask for guidance. Do not start training on a shared GPU — it will slow both jobs and may cause OOM.
- If only small processes (< 500MB) are present: safe to proceed.

### Step 1: Prepare Execution

1. Read the node's configuration from experiment_tree.json:
   - `approach`: what this experiment does
   - `hyperparameters`: training configuration
   - `code_path`: path to the method implementation
   - `config_path`: path to the config file
2. Verify the code file exists and is syntactically valid.
3. Verify the config file exists.
4. Verify the dataset is accessible.
5. Estimate runtime and check against GPU budget.
6. **Verify training invocation** (REQUIRED): Determine the correct command to launch training. If the training script uses package-relative imports (`from src.X import ...`), it MUST be run as `python -m src.train`, NOT `python3 src/train.py` (the latter causes `ModuleNotFoundError`). Test: `python -m {module} --config {config_path} --help` or a 0-step dry run. Do NOT assume `code_path` in experiment_tree.json is the executable entry point — it may reference the model implementation file, not the training script.

### Step 2: Write Experiment Code (if needed)

If the node requires new code (e.g., Stage 4.2 child with modified hyperparameters):
1. Copy parent's code as starting point.
2. Apply the specified modifications.
3. Save to the node's code_path.
4. Verify the modified code runs on a minimal test.

If the node requires method changes (Stage 4.3):
1. Read parent's code and results.
2. Analyze what to improve based on parent's error patterns.
3. Implement the specified improvement.
4. Save and verify.

If the node is an ablation (Stage 4.4):
1. Copy the winning method's code.
2. Remove the specified component.
3. Save and verify.

### Step 2.5: Update Node Status to "running" (MANDATORY — before training)

**IMMEDIATELY before starting any training**, update experiment_tree.json:
- Set `node["status"] = "running"`
- Set `node["start_time"] = "<ISO timestamp>"`
- Write the updated tree to disk

This is critical for tracking, resume, and budget. Do NOT leave status as "runnable" during training.

### Step 3: Git Pre-Registration

Before submitting the job, commit the experiment design (including the status update):
```bash
git add experiment_tree.json configs/{node_id}.yaml
git commit -m "research(protocol): {node_id} — {approach_description}"
```

### Step 4: Submit GPU Job

**Determine the correct training command first.** If the training script uses package imports, use `python -m` (e.g., `python -m src.train`). See Step 1.6.

**Via SSH MCP** (if `config.yaml` has `mcp.ssh_remote: true`):
- Use `mcp__ssh__execute_command` on the configured SSH host:
  ```
  cd /path/to/project && nohup python -m src.train --config {config_path} > results/{node_id}/logs/train.log 2>&1 &
  ```

**Via Python scripts** (fallback):
```bash
python3 scripts/gpu_submit.py \
  --node {node_id} \
  --script {training_script} \
  --config {config_path} \
  --gpu-type {gpu_type}
```
Note: gpu_submit.py auto-converts package-style script paths (e.g., `src/train.py` → `python -m src.train`) to avoid ImportError from package-relative imports. It also supports `--resume` for checkpoint recovery.

**Via direct execution** (simplest for local GPU):
```bash
nohup python -m {training_module} --config {config_path} --node_id {node_id} > results/{node_id}/train.log 2>&1 &
```
Determine the correct module path from README_code.md or the training script's docstring (e.g., `src.train` for `src/train.py`).

Record the returned `job_id` or PID.

### Step 5: Poll for Completion

**Via SSH MCP** (if used for submission):
- Use `mcp__ssh__execute_command`: `cat results/{node_id}/metrics.json 2>/dev/null`
- Repeat until file exists and is valid JSON.

**Via Python scripts** (fallback):
```bash
python3 scripts/gpu_poll.py --node {node_id} --timeout {timeout_seconds}  # value is in seconds, not minutes
```

Poll behavior:
- Check every 30 seconds for short jobs (< 10 min estimated).
- Check every 2 minutes for longer jobs.
- Timeout: 2x estimated runtime.
- If timeout: check if partial results exist, decide whether to extend or abort.

### Step 6: Collect Results

On success:
1. Read `results/{node_id}/metrics.json` — verify it has the expected metrics.
2. Read training logs for any warnings or anomalies.
3. Check for NaN values, unreasonable metric values.
4. Sanity check: is the result within a plausible range?

On failure:
1. Read error logs from `results/{node_id}/logs/`.
2. Classify the failure:
   - **OOM**: out of memory — reduce batch size or model size
   - **NaN/Inf**: numerical instability — reduce learning rate, add gradient clipping
   - **Data error**: missing files, wrong format — fix data pipeline
   - **Code bug**: runtime error — debug and fix
   - **Timeout**: experiment too slow — optimize or reduce scope
3. Log to `.ai/evolution/negative-results.md`.
4. If fixable: apply fix and re-submit (max 2 retries per node). **If `resume.pt` exists** in the node's checkpoint directory (see `train_cfg.checkpoint_dir` / node_id), use `--resume` to continue from the last eval checkpoint rather than restarting from scratch.
5. If unfixable: mark node as `buggy` with detailed notes.

### Step 7: Generate Figures

For completed experiments, generate standard figures:

1. **Learning curve**: loss vs. epoch/step
2. **Metric progression**: primary metric vs. training progress
3. **Comparison bar chart**: this node vs. baselines (if baselines have run)
4. **Method-specific figures**: as defined in the experiment plan

Save to `results/{node_id}/figures/`.

Use matplotlib with publication-quality settings:
- Font size >= 12
- DPI >= 300
- Clear axis labels and legends
- Color-blind friendly palette

### Step 8: VLM Figure Review

For each generated figure:
1. Invoke VLM review logic (see `vlm_review.md`).
2. If score >= 4: figure approved.
3. If score < 4: read feedback, regenerate figure, re-review.
4. Max 3 regeneration attempts.

### Step 9: Git Result Commit

After collecting results, commit them:
```bash
git add results/{node_id}/ experiment_tree.json
git commit -m "research(results): {node_id} — {primary_metric}={value}"
```

### Step 10: Update State

Update the node in experiment_tree.json:
```json
{
  "status": "complete" | "buggy",
  "results": {
    "primary_metric": value,
    "secondary_metrics": { ... },
    "runtime_seconds": N,
    "gpu_hours": N
  },
  "figures": ["results/{node_id}/figures/{name}.png", ...],
  "figures_approved": true | false,
  "completion_date": "{date}",
  "notes": "any relevant observations"
}
```

## Output

| File | Action |
|------|--------|
| `results/{node_id}/metrics.json` | Write experiment results |
| `results/{node_id}/config.json` | Write experiment configuration |
| `results/{node_id}/figures/` | Generate experiment figures |
| `results/{node_id}/logs/` | Save training logs |
| `experiment_tree.json` | Update node status and results |

## .ai/ Updates

| File | Action |
|------|--------|
| `.ai/evolution/experiment-log.md` | (updated by memory_sync — do not write directly) |
| `.ai/evolution/negative-results.md` | (updated by memory_sync — do not write directly) |

## Rules

- Fix all random seeds before execution for reproducibility.
- Save checkpoints for experiments > 30 minutes.
- **Checkpoint resume for long runs**: Experiments > 1 hour MUST use a training script that supports `--resume`. A single `resume.pt` in the node's checkpoint directory (overwritten each eval) is sufficient — do not accumulate checkpoints that fill disk. `resume.pt` is automatically deleted after successful completion.
- Never modify another node's results.
- If a node takes > 2x estimated time, investigate before waiting longer.
- Always validate results before marking as complete (no NaN, reasonable range).
- Log GPU hours consumed for budget tracking.
- **Never delete or overwrite existing training logs or results.** If `results/{node_id}/metrics.json` already exists with valid data, skip training. If log files exist, back them up with a timestamp before starting a new run. Losing hours of training data to a careless restart is unrecoverable.

## When Done

- `results/{node_id}/` contains metrics.json, config.json, figures/, logs/.
- experiment_tree.json node is updated with status and results.
- Experiment logged in `.ai/evolution/experiment-log.md`.
- Return: `{node_id}` status, primary metric value, any concerns.
