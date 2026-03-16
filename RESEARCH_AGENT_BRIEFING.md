# Research Agent — Briefing

You are scaffolding a fully automated research pipeline driven by Claude Code.
Given a research direction, the system autonomously delivers: a peer-review-quality paper (PDF), 
a clean code repository, and organized experimental results — without human intervention after kickoff.

---

## Design Principles (learned from AI Scientist v2, FARS, CycleResearcher, Agent Laboratory)

1. **Direction alignment before autonomy** — 30min co-pilot session to lock research question before unattended run
2. **Tree search over linear execution** — experiments branch and compete, best path wins
3. **Role-based agent team** — specialized agents (not generic ones) for each phase
4. **Research-Review-Refinement cycle** — writing and reviewing loop until quality threshold
5. **VLM figure quality gate** — every plot reviewed by vision model before paper inclusion
6. **Novelty verification** — Semantic Scholar check before committing to an idea
7. **AgentInfra knowledge layer** — .ai/ persists all findings, decisions, and context across sessions

---

## Phase 0 — Direction Alignment (user present, ~30 min)

Goal: lock a research question that is novel, feasible, and scoped to available resources.

```
Clarification Agent
  Q1: What phenomenon or problem interests you? What's your intuition about it?
  Q2: What do you know about existing work? What's the gap?
  Q3: What compute and time do you have? (GPU hours, deadline)

Novelty Check Agent
  → search Semantic Scholar for top-20 related papers
  → check if proposed direction is already well-covered
  → if saturated: propose 3 adjacent directions that have gaps
  → user selects or modifies

Output: RESEARCH_PROPOSAL.md
  - research_question: one sentence
  - hypothesis: testable claim
  - proposed_method: high-level approach
  - baselines: what to compare against
  - success_metric: exact measurement (e.g., "accuracy > 0.85 on dataset X")
  - compute_budget: GPU hours available
  - deadline: target submission date

User /approve → RESEARCH_PROPOSAL.md locked → pipeline starts
```

---

## Phase 1 — Research Pipeline (unattended)

### Stage structure

Each stage ends with a judge gate. Judge fail → fix and retry. Judge pass → advance.
Stages S3–S5 use tree search instead of linear execution.

---

### S0 · Init
```
Read RESEARCH_PROPOSAL.md
Bootstrap .ai/ knowledge base:
  .ai/core/research-context.md   ← research question + hypothesis
  .ai/core/methodology.md        ← planned approach
  .ai/evolution/decisions.md     ← all major decisions (ADR format)
Write CLAUDE.md
Initialize experiment_tree.json (empty, all nodes pending)
git init + first commit
```

---

### S1 · Literature Survey
```
Agent role: PhD agent

Tools: Semantic Scholar API, arXiv API, web search
Process:
  1. Search for top-50 papers related to research question
  2. For each paper: read abstract + intro + conclusion
  3. Cluster into themes
  4. Identify: what methods exist, what gaps exist, what baselines are standard
  5. Flag top-10 most relevant for deep reading

Output:
  RELATED_WORK.md          — structured survey with citations
  BASELINES.md             — standard baselines + their reported numbers
  .ai/core/literature.md   — key findings for agent context
  bibliography.bib         — BibTeX entries

Judge gate: ≥20 papers reviewed, ≥3 baselines identified, gap clearly stated
```

---

### S2 · Ideation + Experimental Design
```
Agent roles: PhD agent + Postdoc agent (debate structure)

Process:
  1. PhD agent generates 5 concrete hypotheses from the literature gap
  2. For each hypothesis: estimate feasibility × novelty × impact score
  3. Postdoc agent critiques each hypothesis
  4. Select top-2 hypotheses for parallel tree search in S3
  5. Design experiment_tree.json:
     - root nodes: N=3 independent implementations per hypothesis
     - each node: {id, hypothesis, approach, code_plan, metric, status, score, children}

Output:
  experiment_tree.json     — tree structure, all nodes status=pending
  EXPERIMENT_PLAN.md       — human-readable version
  .ai/core/methodology.md  — updated with selected approach

Judge gate: ≥2 hypotheses selected, experiment tree has ≥6 root nodes, 
           each node has clear success metric
```

---

### S3 · Code Implementation (Assets)
```
Agent role: ML Engineer agent

Process:
  1. Read BASELINES.md → implement all baselines first
  2. For each root node in experiment_tree.json:
     - implement method code
     - implement evaluation harness
     - verify: does it run without errors on a small test case?
     - status: buggy | runnable

Output:
  src/
    method/         ← proposed method implementation
    baselines/      ← baseline implementations  
    evaluation/     ← evaluation scripts
    utils/          ← shared utilities
  requirements.txt
  README_code.md   ← how to reproduce every experiment

Judge gate: all root nodes status=runnable, baselines verified against 
           their reported numbers (±5% tolerance)
```

---

### S4 · Experiment Tree Search (core loop)
```
Agent role: Experiment Manager agent (orchestrates tree)
           + ML Engineer agent (executes nodes)

This is the most critical stage. Uses progressive tree search.

Tree search algorithm:
  Stage 4.1 — Preliminary Investigation
    Run all root nodes (N=3 per hypothesis, parallel where possible)
    For each node:
      - run experiment
      - save results to results/{node_id}/metrics.json
      - generate figures with matplotlib
      - VLM review figures (see VLM gate below)
      - classify: buggy (error/unreasonable result) | non-buggy (ran + plausible result)
    Select best non-buggy node per hypothesis → becomes root of Stage 4.2

  Stage 4.2 — Hyperparameter Tuning
    From each Stage 4.1 winner, create child nodes with varied hyperparameters
    Run child nodes, evaluate, select best → root of Stage 4.3

  Stage 4.3 — Method Refinement
    From Stage 4.2 winner, create child nodes with method improvements
    (different architecture choices, different training strategies, etc.)
    Run, evaluate, select best → root of Stage 4.4

  Stage 4.4 — Ablation Studies
    From Stage 4.3 winner, create ablation nodes
    (remove each component to measure its contribution)
    Run all ablations → final results

VLM figure gate (applied after every node):
  - Pass figure image to VLM
  - Check: axis labels present? legend present? 
           title descriptive? values readable? no overlapping text?
  - Fail → mark node as buggy for figures, regenerate
  - Pass → figures approved

Output:
  results/
    {node_id}/
      metrics.json      ← all numerical results
      figures/          ← approved figures
      config.json       ← exact hyperparameters used
  experiment_tree.json  ← fully populated with scores + winners
  RESULTS_SUMMARY.md    ← best results across all nodes

Judge gate: Stage 4.4 complete, ≥1 method outperforms all baselines 
           on primary metric, all figures VLM-approved
```

---

### S5 · Analysis + Significance Testing
```
Agent role: Postdoc agent

Process:
  1. Run statistical significance tests (t-test, bootstrap CI) on main results
  2. Error analysis: where does the method fail? Why?
  3. Qualitative analysis: case studies, examples
  4. Compute all numbers that will appear in paper tables

Output:
  ANALYSIS.md          ← statistical results + interpretations
  tables/              ← LaTeX-ready table files
  figures/analysis/    ← additional analysis figures (VLM-reviewed)

Judge gate: significance tests run, p-values computed, error analysis present
```

---

### S6 · Paper Writing
```
Agent role: Writing agent (reads all prior outputs as structured inputs)

Inputs (not blank slate — all pre-populated):
  RELATED_WORK.md    → Section 2
  EXPERIMENT_PLAN.md → Section 3 (Method)
  RESULTS_SUMMARY.md → Section 4 (Experiments)
  ANALYSIS.md        → Section 4 continued
  bibliography.bib   → References

Process:
  1. Write Abstract (last, after everything else)
  2. Write Introduction (problem + gap + contributions)
  3. Write Related Work (from RELATED_WORK.md, reorganized for narrative)
  4. Write Method (from EXPERIMENT_PLAN.md + .ai/core/methodology.md)
  5. Write Experiments (from tables/ + figures/ + RESULTS_SUMMARY.md)
  6. Write Conclusion
  7. Write Abstract
  8. Compile LaTeX → check it compiles without errors → generate PDF

Output:
  paper/
    main.tex
    sections/          ← one .tex file per section
    figures/           ← symlinked from approved figures
    bibliography.bib
  paper.pdf

Judge gate: LaTeX compiles, PDF renders correctly, all figures present,
           all cited references in bibliography
```

---

### S7 · Review-Revise Cycle
```
Agent roles: Reviewer agent × 3 (different reviewer personas) + Writing agent

This stage runs as a loop until target score is reached.

Reviewer personas:
  R1: Methods-focused reviewer (skeptical of technical claims, wants ablations)
  R2: Clarity-focused reviewer (wants clear writing, motivation, examples)  
  R3: Novelty-focused reviewer (compares to related work, questions contribution)

Each review cycle:
  1. Three reviewers independently score paper on:
     - Soundness: 1-4
     - Presentation: 1-4  
     - Contribution: 1-4
     - Overall: 1-10
  2. Each reviewer lists: strengths, weaknesses, questions
  3. Writing agent addresses every weakness:
     - Critical weakness → revise or add experiment
     - Minor weakness → clarify in text
     - Question → add to paper or respond in writing
  4. Recompile PDF
  5. Re-review
  6. Repeat until: average overall score ≥ 6.0 OR 3 cycles completed

Output:
  reviews/
    cycle_{N}/
      review_R1.md
      review_R2.md
      review_R3.md
      response.md       ← writing agent's response to each point
  paper_v{N}.pdf

Judge gate: average score ≥ 6.0 OR 3 revision cycles complete
```

---

### S8 · Delivery
```
Process:
  1. Final paper compilation with clean formatting
  2. Code repository cleanup:
     - remove debug code
     - add docstrings
     - verify README_code.md reproduces all experiments
     - run all experiments one final time to confirm reproducibility
  3. Package results:
     DELIVERY/
       paper.pdf
       code/            ← clean repository
       results/         ← all experimental results + figures
       README.md        ← how to reproduce everything
  4. Write DELIVERY.md summary
  5. Notify user

Judge gate: paper.pdf renders, code runs from README_code.md, 
           all results in DELIVERY/ match numbers in paper
```

---

## Agent Roles Summary

| Agent | Phase | Responsibility |
|-------|-------|---------------|
| Clarification | P0 | Extract research direction from user |
| Novelty Check | P0 | Semantic Scholar gap analysis |
| PhD | S1, S2 | Literature survey, hypothesis generation |
| Postdoc | S2, S5 | Hypothesis critique, statistical analysis |
| ML Engineer | S3, S4 | Code implementation, experiment execution |
| Experiment Manager | S4 | Tree search orchestration, node selection |
| Writing | S6, S7 | Paper writing and revision |
| Reviewer (×3) | S7 | Peer review simulation (3 personas) |
| Judge | Every stage | Quality gate pass/fail |

---

## Key Files

### experiment_tree.json (node format)
```json
{
  "id": "h1-root-2",
  "stage": "4.1",
  "hypothesis": "attention mechanism improves X",
  "approach": "add cross-attention layer between encoder and decoder",
  "parent": null,
  "children": ["h1-s42-1", "h1-s42-2", "h1-s42-3"],
  "status": "complete",
  "classification": "non-buggy",
  "score": 0.847,
  "primary_metric": "accuracy",
  "metric_value": 0.847,
  "config": {"lr": 0.001, "layers": 3, "heads": 8},
  "figures_approved": true,
  "results_path": "results/h1-root-2/metrics.json"
}
```

### registry.yaml
```yaml
phase: "research"
current_stage: "S1"
stages:
  S0: { status: complete }
  S1: { status: running, papers_reviewed: 0, target: 20 }
  S2: { status: pending }
  S3: { status: pending }
  S4: { status: pending, tree_stages_complete: 0, tree_stages_total: 4 }
  S5: { status: pending }
  S6: { status: pending }
  S7: { status: pending, review_cycles: 0, current_score: 0 }
  S8: { status: pending }
target_venue: ""
target_score: 6.0
```

### config.yaml (user fills)
```yaml
research_direction: ""     # your research interest — one sentence or paragraph
target_venue: ""           # e.g. "NeurIPS 2026", "ICML 2026", or "arxiv"
target_score: 6.0          # minimum average reviewer score to accept
compute:
  gpu_hours: 100           # available GPU budget
  gpu_type: "A100"         # GPU type available
  parallel_jobs: 3         # how many experiments to run in parallel
resources:
  semantic_scholar_key: "" # optional, for higher API throughput
notify:
  email: ""
  telegram: ""
```

---

## VLM Figure Review Protocol

Applied after every figure generation in S4 and S5.

```
Pass figure as image to VLM. Ask:
  1. Are axis labels present and descriptive?
  2. Is a legend present (if multiple series)?
  3. Is the title informative?
  4. Are all values readable (no overlapping text)?
  5. Does the figure clearly show what the caption claims?

Score: 1-5
≥ 4: approved
< 4: rejected → regenerate with specific feedback from VLM
Max 3 regeneration attempts → if still failing, flag for human review
```

---

## Novelty Verification Protocol

Applied in Phase 0 before /approve.

```
Search Semantic Scholar for:
  - exact research question keywords
  - proposed method name
  - combination of method + dataset + metric

For each result:
  - read title + abstract
  - compute similarity to proposed direction (high/medium/low)

If ≥3 high-similarity papers found:
  - report: "This direction appears well-covered. Here are the gaps:"
  - propose 3 adjacent directions with lower coverage
  - user selects or modifies

If < 3 high-similarity papers:
  - proceed with proposed direction
  - add found papers to bibliography.bib
```

---

## .ai/ Knowledge Layer (AgentInfra)

Every agent reads .ai/ before touching any code or papers.
Every agent updates .ai/ after completing their work.

```
.ai/
  core/
    research-context.md    ← research question, hypothesis, success metric
    methodology.md         ← proposed method, current best implementation
    literature.md          ← key papers, baselines, known results
  evolution/
    decisions.md           ← all major decisions in ADR format (append-only)
    negative-results.md    ← what was tried and didn't work (crucial!)
    experiment-log.md      ← brief log of every experiment run
  _loading-rules.md        ← which agent loads which docs
  _maintenance-rules.md    ← drift detection protocol
```

Critical: `.ai/evolution/negative-results.md` — every failed experiment node records why it failed. This prevents later agents from repeating failed approaches and accelerates the search.

---

## What This Produces

```
DELIVERY/
  paper.pdf                     ← peer-review-quality paper
  paper_v1.pdf, v2.pdf, v3.pdf  ← revision history
  code/
    src/                        ← clean implementation
    README_code.md              ← exact reproduction steps
    requirements.txt
  results/
    experiment_tree.json        ← full tree with all results
    {winning_node}/
      metrics.json
      figures/
  reviews/
    cycle_1/, cycle_2/, ...     ← all reviewer feedback + responses
  DELIVERY.md                   ← summary for human
```
