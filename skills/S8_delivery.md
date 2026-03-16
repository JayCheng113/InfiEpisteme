# S8 Delivery — Final Packaging

> Stage 8. Package all deliverables for final output.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S8`.
2. Read `config.yaml` — target venue for any final formatting.
3. Verify all prerequisite files exist:
   - `paper.pdf` — compiled paper
   - `src/` — implementation code
   - `results/` — experiment results
   - `README_code.md` — reproduction instructions
   - `RESULTS_SUMMARY.md` — results overview
   - `ANALYSIS.md` — analysis
   - `bibliography.bib` — references
4. Check `state/JUDGE_RESULT.json` — if retrying, read `retry_guidance`.

### Idempotency Check
- If `DELIVERY/` directory exists with all expected files: verify completeness and skip.
- If partial: complete missing items.

## Your Role

You package everything into a clean, reproducible delivery. You verify consistency between paper numbers and actual results, clean up code, and create a self-contained package.

## Process

### Step 1: Verify Paper-Result Consistency

Critical check: every number in the paper must match the actual results.

1. Extract all numerical claims from `paper/sections/experiments.tex`:
   - Main results table values
   - Ablation table values
   - Any inline numerical claims
2. Cross-reference with `results/*/metrics.json`.
3. If ANY mismatch is found:
   - Fix the paper (not the results).
   - Recompile PDF.
   - Log the discrepancy.

### Step 2: Clean Up Code

1. **Remove debug code**: Remove print statements, commented-out code blocks, debug flags.
2. **Add docstrings**: Every module, class, and public function must have a docstring.
3. **Verify imports**: Remove unused imports.
4. **Check secrets**: Ensure no API keys, passwords, or credentials in the code.
5. **Format**: Run a formatter if available (black for Python).
6. **Lint**: Fix any obvious lint warnings.

Do NOT change functionality — only clean up presentation.

### Step 3: Verify Reproducibility

Walk through `README_code.md` mentally (or actually run key commands):
1. Can someone install dependencies from requirements.txt?
2. Are all dataset paths configurable (not hardcoded)?
3. Are all experiment configs present in configs/?
4. Does the evaluation command work?
5. Are random seeds documented?

Fix any issues found.

### Step 4: Create DELIVERY/ Package

```
DELIVERY/
  paper.pdf              # final paper
  code/                  # clean code
    src/                 # copied from src/
    configs/             # experiment configurations
    requirements.txt     # dependencies
    README.md            # reproduction instructions (from README_code.md)
  results/               # key results
    main_results.json    # primary comparison table data
    ablation_results.json # ablation data
    figures/             # key figures used in paper
  supplementary/         # optional
    full_results/        # all experiment results
    reviews/             # review history
    analysis/            # detailed analysis
```

### Step 5: Create DELIVERY/README.md

```markdown
# {Paper Title}

## Paper
See `paper.pdf` for the full paper.

## Quick Start
cd code
pip install -r requirements.txt
# Reproduce main results:
python src/evaluation/evaluate.py --method ours --config configs/best.yaml

## Repository Structure
- `code/src/method/` — proposed method implementation
- `code/src/baselines/` — baseline implementations
- `code/src/evaluation/` — evaluation scripts
- `code/configs/` — experiment configurations
- `results/` — key experimental results
- `supplementary/` — additional materials

## Reproducing Experiments
{Condensed from README_code.md — step by step instructions}

## Key Results
{Brief summary of main findings with numbers}

## Citation
@article{...}
```

### Step 6: Write DELIVERY.md

Summary document at the project root:

```markdown
# Delivery Summary

## Paper
- **Title**: {title}
- **Target Venue**: {venue}
- **Pages**: {count}
- **Final Review Score**: {score} (after {N} review cycles)

## Key Results
| Method | {Primary Metric} |
|--------|-----------------|
| Baseline 1 | {value} |
| Baseline 2 | {value} |
| **Ours** | **{value}** |

## Deliverables
- `DELIVERY/paper.pdf` — final paper
- `DELIVERY/code/` — clean, documented code
- `DELIVERY/results/` — reproducible results
- `DELIVERY/supplementary/` — review history and detailed analysis

## Verification
- [ ] Paper numbers match results/{node_id}/metrics.json
- [ ] Code runs from README instructions
- [ ] All figures in paper are in DELIVERY/results/figures/
- [ ] Bibliography entries verified against real papers

## Timeline
- Direction alignment: {date}
- Literature survey: {date}
- Experiments completed: {date}
- Paper written: {date}
- Review cycles: {N}
- Delivered: {date}
```

### Step 7: Final PDF Check

One last verification of paper.pdf:
1. Open and verify it renders (page count > 0).
2. Check all figures are visible.
3. Check bibliography renders.
4. Check no "??" undefined references.
5. Check page count is within venue limits.

## Output

| File | Action |
|------|--------|
| `DELIVERY/paper.pdf` | Copy final paper |
| `DELIVERY/code/` | Clean code package |
| `DELIVERY/code/README.md` | Reproduction instructions |
| `DELIVERY/results/` | Key results and figures |
| `DELIVERY/supplementary/` | Additional materials |
| `DELIVERY.md` | Delivery summary |

## Quality Criteria (from PIPELINE.md)

- [ ] paper.pdf renders correctly
- [ ] Code runs from DELIVERY/README.md instructions
- [ ] Results in DELIVERY/results/ match numbers in paper
- [ ] DELIVERY.md summary present

## Rules

- Do not modify experiment results — only fix the paper if numbers disagree.
- Do not add new experiments at this stage.
- Keep the code clean but functionally identical to what produced the results.
- Ensure no credentials or API keys are included in the delivery.
- The delivery must be self-contained — no dependencies on the pipeline infrastructure.

## When Done

- `DELIVERY/` is fully populated with all files.
- `DELIVERY.md` summarizes the project.
- Paper numbers verified against actual results.
- Code is clean and documented.
- Commit: `S8: final delivery package`
- Pipeline is COMPLETE.
