# S2 Ideation — Hypothesis Generation and Experimental Design

> Stage 2. Multi-perspective ideation fused with experiment planning.
> Inherits: `_common.md`

## Before You Start

1. Read `registry.yaml` — confirm `current_stage: S2`.
2. Read `RESEARCH_PROPOSAL.md` — research question, hypothesis, proposed method.
3. Read `RELATED_WORK.md` — literature landscape and gap.
4. Read `BASELINES.md` — known baselines and their numbers.
5. Read `bibliography.bib` — available references.
6. Read `.ai/core/methodology.md` — current methodology notes.
7. Read `.ai/core/literature.md` — key themes and gap.
8. Read `.ai/evolution/decisions.md` — prior decisions.
9. Read `hardware_profile.json` — hardware capabilities. Your hypotheses must be feasible on the available hardware. If no GPU is available, do not propose GPU-intensive approaches without noting SSH remote execution requirement.
10. Check `state/JUDGE_RESULT.json` — if retrying, focus on failed criteria (e.g., "hypotheses lack feasibility scores", "experiment tree missing root nodes").

### Idempotency Check
- If `EXPERIMENT_PLAN.md` and `experiment_tree.json` (with populated nodes) already exist and no retry: verify completeness and skip.

## Your Role

You generate research hypotheses, subject them to multi-perspective debate, score them, and design a concrete experiment tree. This is the creative core of the pipeline.

## Process

### Step 0: Determine What Experimental Design This Research Needs

Before generating hypotheses or designing experiments, read `RESEARCH_PROPOSAL.md`, `RELATED_WORK.md`, `config.yaml` (target venue, compute budget), and `hardware_profile.json`. Then answer:

1. **What type of paper is this?** A method paper (propose something new), a benchmark paper (systematic comparison), a negative result paper (X doesn't work and here's why), or a hybrid? The experimental design depends entirely on this.
2. **What would a reviewer at {target_venue} need to see?** A method paper needs strong baselines and ablations. A benchmark paper needs controlled conditions across multiple axes (architectures, scales). An analysis paper needs depth over breadth.
3. **How many independent variables can the budget support?** Compute `available_hours / estimated_hours_per_run` to get max experiments. Design within this constraint, not over it.
4. **What comparison axes matter for this specific claim?** Not all research needs multiple architectures or scales. A method paper comparing two specific approaches might only need one architecture at one scale with thorough ablation. A generalizability claim needs multiple.
5. **What are the minimum experiments needed to support the paper's core claim?** Start from the claim, work backward to the experiments — don't start from a template.

Write your answers as the first section of `EXPERIMENT_PLAN.md`. The experiment tree design below should follow from these answers, not from a fixed formula.

### Step 1: Generate Hypotheses

From the literature gap identified in RELATED_WORK.md, generate **up to 5 concrete hypotheses** (fewer is fine if the research question is narrow). Each hypothesis must be:
- **Testable**: can be verified or falsified by an experiment
- **Specific**: names the method, dataset, and expected outcome
- **Grounded**: motivated by a gap in the literature
- **Feasible**: achievable within the compute budget in config.yaml AND the hardware capabilities in hardware_profile.json

Format for each:
```
H{N}: {One-sentence hypothesis — phrased as a question if unverified}
- Motivation: {Why this hypothesis is worth testing, citing the gap}
- Approach: {How to test it — 2-3 sentences}
- Expected outcome: {What you expect to observe if true}
- Risk: {What could go wrong}
- Evidence basis: {empirical | theoretical | speculative}
  - empirical: supported by published experimental data (cite the paper)
  - theoretical: grounded in formal theory but no direct experiments
  - speculative: LLM reasoning without literature support — FLAG THIS CLEARLY
```

**Anti-hallucination rule for hypotheses**: If your hypothesis makes a claim about how a method performs (e.g., "X underperforms on Y"), you MUST cite the specific paper and result that supports this. If no such evidence exists, mark the hypothesis as `speculative` and phrase it as a question ("Does X underperform on Y?"), not an assertion. Reviewers and the Judge will reject assertions presented as fact without evidence.

### Step 2: Multi-Perspective Debate

Evaluate all 5 hypotheses from 6 different viewpoints. You adopt each perspective in turn, producing a structured critique. This is a single-agent process — you simulate each perspective.

**Perspective 1: Innovator**
Focus: novel combinations, creative leaps, unexplored connections.
- Which hypotheses combine ideas in genuinely new ways?
- Are there more creative variants that push further?
- Score each hypothesis on novelty (1-5).

**Perspective 2: Pragmatist**
Focus: engineering feasibility, implementation complexity, compute budget, hardware constraints.
- Can this be implemented in the available time?
- Does the compute budget support the required experiments?
- Does the available hardware (from `hardware_profile.json`) support the model size and training requirements?
- Are the required datasets available?
- Score each hypothesis on feasibility (1-5).

**Perspective 3: Theorist**
Focus: mathematical rigor, theoretical grounding, formal guarantees.
- Is there a theoretical reason to expect this to work?
- What assumptions does this rely on? Are they reasonable?
- Can the approach be analyzed formally?
- Score each hypothesis on theoretical soundness (1-5).

**Perspective 4: Contrarian**
Focus: challenge assumptions, identify blind spots, find fatal flaws.
- What assumption, if wrong, would invalidate this hypothesis?
- Has something similar been tried and failed? (Check negative-results.md)
- Is the expected improvement realistic?
- Flag any hypotheses that should be eliminated.

**Perspective 5: Interdisciplinary**
Focus: cross-domain analogies, techniques from other fields.
- Does a similar problem exist in another field with known solutions?
- Can techniques from {adjacent field} improve this approach?
- Are there overlooked connections?

**Perspective 6: Empiricist**
Focus: experiment-first methodology, measurability, reproducibility.
- Is the success metric well-defined and measurable?
- Can baselines be fairly compared?
- What confounding variables exist?
- Is the evaluation protocol sound?
- Score each hypothesis on measurability (1-5).

### Step 3: Score and Rank

Compute a composite score for each hypothesis:

```
Score = Feasibility(1-5) x Novelty(1-5) x Impact(1-5)
```

Where Impact = average of (theoretical soundness + measurability) / 2, adjusted by Contrarian/Interdisciplinary insights.

Rank all 5 hypotheses by composite score.

### Step 4: Select Hypotheses for Testing

Select the top hypotheses for experimental investigation (typically 2, but adjust based on Step 0 — a focused method paper may need only 1, a broad benchmark may need 3+). Justify:
- Why these two (not others)
- How they complement each other (ideally, they test different aspects)
- What the fallback is if both fail

Record this decision in `.ai/evolution/decisions.md` as ADR-002.

### Step 5: Design Experiment Tree

For each selected hypothesis, create root nodes (the number depends on your Step 0 analysis — a systematic comparison might need 6+, a focused ablation study might need 3). Each root node is a different concrete instantiation of the hypothesis.

**CRITICAL: One node = one training run.** Each node must correspond to exactly ONE model trained with ONE configuration. If a hypothesis requires comparing N methods, create N separate nodes — do NOT pack multiple training runs into a single node. Example:
- WRONG: `H1_R1: "Compare PreNorm, AttnRes, DCA, MUDDFormer"` (4 training runs in 1 node)
- RIGHT: `H1_R1: "PreNorm baseline"`, `H1_R2: "Block AttnRes"`, `H1_R3: "DCA"` (1 run each)

**Budget estimation per node**: Before finalizing the tree, estimate GPU hours per node:
- Estimate throughput based on hardware and model size (approximate: A100-40GB ~50K tok/s for 0.5B bf16, ~25K for 1.5B; A100-80GB ~2x; V100 ~0.3x)
- Calculate: `gpu_hours = total_tokens / tokens_per_sec / 3600`
- Sum all nodes. If total exceeds `config.yaml compute.gpu_hours`, reduce scope:
  - Cut token count (S4.1 preliminary: 100-200M tokens is sufficient)
  - Drop lowest-priority nodes
  - Merge similar hypotheses

Root node structure:
```json
{
  "id": "H{h}_R{r}",
  "hypothesis": "H{h}",
  "stage": "4.1",
  "approach": "description of this specific variant",
  "key_difference": "what makes this variant unique",
  "hyperparameters": {},
  "estimated_gpu_hours": 0,
  "success_metric": "metric_name",
  "status": "pending",
  "parent": null,
  "children": [],
  "results": null
}
```

Write the full experiment tree to `experiment_tree.json`:
```json
{
  "nodes": [ ... ],
  "metadata": {
    "created": "{date}",
    "last_updated": "{date}",
    "current_stage": "4.1",
    "hypotheses": {
      "H1": "{hypothesis text}",
      "H2": "{hypothesis text}"
    }
  }
}
```

## Output Files

### EXPERIMENT_PLAN.md

Use template from `templates/EXPERIMENT_PLAN.md`:

```markdown
# Experiment Plan

## Selected Hypotheses

### H1: {Hypothesis}
- **Feasibility**: {score}/5
- **Novelty**: {score}/5
- **Impact**: {score}/5
- **Approach**: {description}

### H2: {Hypothesis}
...

## Multi-Perspective Debate Summary
{Key insights from the 6-perspective debate — 1-2 paragraphs}

## Eliminated Hypotheses
{H3, H4, H5 — why they were not selected}

## Experiment Tree

### Root Nodes (Stage 4.1)
| Node ID | Hypothesis | Approach | Key Difference |
|---------|-----------|----------|----------------|
| H1_R1   | H1        | ...      | ...            |
| ...     | ...       | ...      | ...            |

## Evaluation Protocol
- **Primary Metric**: {metric name and definition}
- **Secondary Metrics**: {list}
- **Dataset**: {name, size, splits}
- **Evaluation Script**: src/evaluation/evaluate.py
```

### experiment_tree.json

Populated with 6 root nodes as described above.

## .ai/ Updates

| File | Action |
|------|--------|
| `.ai/core/methodology.md` | (updated by memory_sync — do not write directly) |
| `.ai/evolution/decisions.md` | (updated by memory_sync — do not write directly) |

## Quality Criteria (from PIPELINE.md)

- [ ] >= 2 hypotheses selected with feasibility/novelty/impact scores
- [ ] Experiment tree has >= 6 root nodes (N=3 per hypothesis)
- [ ] Each node has clear success metric and approach description
- [ ] Multi-perspective critique completed (6 viewpoints documented)

## Rules

- Ground every hypothesis in the literature. No "wouldn't it be cool if..." without evidence.
- Be honest in scoring — do not inflate scores to make hypotheses look better.
- The Contrarian perspective must genuinely challenge. If a hypothesis survives unscathed, the challenge was too soft.
- Root nodes must be meaningfully different from each other — not just hyperparameter variations (that is Stage 4.2's job).
- Do not implement anything — that is S3's job.

## When Done

- `EXPERIMENT_PLAN.md` exists with 2 selected hypotheses, debate summary, and root node table.
- `experiment_tree.json` has 6+ root nodes with status=pending.
- `.ai/core/methodology.md` is updated.
- `.ai/evolution/decisions.md` has ADR-002.
- Commit: `S2: ideation — selected {H1_name} and {H2_name}, 6 root nodes designed`
- Commit: `docs(.ai): update methodology and decisions from S2 ideation`
