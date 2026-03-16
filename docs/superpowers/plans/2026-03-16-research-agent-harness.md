# Research Agent Harness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully automated research pipeline harness driven by Claude Code — given a research direction, it autonomously delivers a peer-review-quality paper (PDF), clean code repository, and organized experimental results.

**Architecture:** Python orchestrator manages pipeline state (registry.yaml, experiment_tree.json) and dispatches Claude Code subagents with role-specific prompts. The `.ai/` knowledge layer (AgentInfra convention) persists all findings, decisions, and context across sessions. Each pipeline stage (S0–S8) has a judge gate that must pass before advancing.

**Tech Stack:** Python 3.11+, PyYAML, Claude Code CLI (subagent dispatch), Semantic Scholar API, arXiv API, matplotlib, LaTeX (paper compilation)

---

## File Structure

```
InfiEpisteme/
├── CLAUDE.md                          # L1 entry point — research pipeline router
├── config.yaml                        # User configuration (compute, APIs, preferences)
├── registry.yaml                      # Pipeline state tracker (current stage, status)
├── experiment_tree.json               # Tree search structure (empty template)
├── requirements.txt                   # Python dependencies
├── run.py                             # CLI entry point
│
├── .ai/                               # AgentInfra knowledge layer (research-adapted)
│   ├── _loading-rules.md              # Research-specific decision tree
│   ├── _maintenance-rules.md          # Research-specific maintenance protocol
│   ├── core/
│   │   ├── architecture.md            # System architecture of the harness itself
│   │   ├── research-context.md        # (generated) Research question + hypothesis
│   │   ├── methodology.md             # (generated) Planned approach
│   │   └── literature.md              # (generated) Key papers + baselines
│   └── evolution/
│       ├── decisions.md               # (generated) All major decisions (ADR format)
│       ├── negative-results.md        # (generated) Failed experiments
│       └── experiment-log.md          # (generated) Every experiment run
│
├── agents/                            # Agent role prompt templates
│   ├── clarification.md               # Phase 0: extract research direction
│   ├── novelty_check.md               # Phase 0: Semantic Scholar gap analysis
│   ├── phd.md                         # S1-S2: literature survey, hypothesis generation
│   ├── postdoc.md                     # S2, S5: hypothesis critique, statistics
│   ├── ml_engineer.md                 # S3-S4: code implementation, experiments
│   ├── experiment_manager.md          # S4: tree search orchestration
│   ├── writing.md                     # S6-S7: paper writing and revision
│   ├── reviewer.md                    # S7: peer review (3 personas)
│   └── judge.md                       # All stages: quality gate evaluation
│
├── src/                               # Orchestrator source code
│   ├── __init__.py
│   ├── orchestrator.py                # Main pipeline driver
│   ├── stage_runner.py                # Individual stage execution
│   ├── experiment_tree.py             # Tree data structure management
│   ├── judge_gate.py                  # Quality gate logic
│   ├── vlm_review.py                  # VLM figure quality gate
│   ├── scholarly.py                   # Semantic Scholar + arXiv API client
│   └── utils.py                       # Registry I/O, config loading, git helpers
│
└── templates/                         # Output document templates
    ├── RESEARCH_PROPOSAL.md           # Phase 0 output template
    ├── RELATED_WORK.md                # S1 output template
    ├── BASELINES.md                   # S1 output template
    ├── EXPERIMENT_PLAN.md             # S2 output template
    └── RESULTS_SUMMARY.md             # S4 output template
```

---

## Chunk 1: Foundation — Config, State, and Utilities

### Task 1: Project configuration and dependencies

**Files:**
- Create: `config.yaml`
- Create: `registry.yaml`
- Create: `experiment_tree.json`
- Create: `requirements.txt`

- [ ] **Step 1: Create config.yaml template**

```yaml
research_direction: ""
target_venue: ""
target_score: 6.0
compute:
  gpu_hours: 100
  gpu_type: "A100"
  parallel_jobs: 3
resources:
  semantic_scholar_key: ""
notify:
  email: ""
  telegram: ""
```

- [ ] **Step 2: Create registry.yaml initial state**

```yaml
phase: "alignment"
current_stage: "P0"
stages:
  P0: { status: pending }
  S0: { status: pending }
  S1: { status: pending, papers_reviewed: 0, target: 20 }
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

- [ ] **Step 3: Create empty experiment_tree.json**

```json
{
  "nodes": [],
  "metadata": {
    "created": null,
    "last_updated": null,
    "current_stage": null
  }
}
```

- [ ] **Step 4: Create requirements.txt**

```
pyyaml>=6.0
requests>=2.31
```

- [ ] **Step 5: Commit**

```bash
git add config.yaml registry.yaml experiment_tree.json requirements.txt
git commit -m "feat: add project configuration and state tracking files"
```

---

### Task 2: Utility module — registry, config, git helpers

**Files:**
- Create: `src/__init__.py`
- Create: `src/utils.py`

- [ ] **Step 1: Create src/__init__.py**

Empty init file.

- [ ] **Step 2: Create src/utils.py**

Functions: `load_config()`, `load_registry()`, `save_registry()`, `advance_stage()`, `load_experiment_tree()`, `save_experiment_tree()`, `git_commit()`.

- [ ] **Step 3: Commit**

```bash
git add src/
git commit -m "feat: add utility module for config/registry/git operations"
```

---

### Task 3: Experiment tree management

**Files:**
- Create: `src/experiment_tree.py`

- [ ] **Step 1: Create experiment_tree.py**

Classes: `ExperimentNode` (dataclass matching the JSON schema from briefing), `ExperimentTree` with methods: `add_node()`, `get_node()`, `get_root_nodes()`, `get_children()`, `get_best_node()`, `set_status()`, `set_score()`, `to_json()`, `from_json()`.

- [ ] **Step 2: Commit**

```bash
git add src/experiment_tree.py
git commit -m "feat: add experiment tree data structure"
```

---

### Task 4: Judge gate logic

**Files:**
- Create: `src/judge_gate.py`

- [ ] **Step 1: Create judge_gate.py**

`JudgeGate` class with per-stage criteria from the briefing. Method `evaluate(stage, context) -> (pass: bool, reasons: list[str])`. Each stage has specific criteria (e.g., S1: ≥20 papers, ≥3 baselines; S4: stage 4.4 complete, ≥1 method outperforms baselines).

- [ ] **Step 2: Commit**

```bash
git add src/judge_gate.py
git commit -m "feat: add judge gate quality evaluation logic"
```

---

### Task 5: VLM figure review

**Files:**
- Create: `src/vlm_review.py`

- [ ] **Step 1: Create vlm_review.py**

`review_figure(image_path) -> (score: int, feedback: str, approved: bool)` — sends figure to Claude vision API with the 5-question checklist from the briefing. `review_all_figures(directory) -> list[ReviewResult]`. Max 3 regeneration attempts.

- [ ] **Step 2: Commit**

```bash
git add src/vlm_review.py
git commit -m "feat: add VLM figure quality review module"
```

---

### Task 6: Semantic Scholar / arXiv API client

**Files:**
- Create: `src/scholarly.py`

- [ ] **Step 1: Create scholarly.py**

Functions: `search_papers(query, limit=50) -> list[Paper]`, `get_paper_details(paper_id) -> Paper`, `check_novelty(query, method, dataset) -> NoveltyResult`, `fetch_bibtex(paper_ids) -> str`. Uses Semantic Scholar API (with optional API key from config).

- [ ] **Step 2: Commit**

```bash
git add src/scholarly.py
git commit -m "feat: add Semantic Scholar and arXiv API client"
```

---

## Chunk 2: Agent Prompts

### Task 7: Agent prompt templates (all 9 agents)

**Files:**
- Create: `agents/clarification.md`
- Create: `agents/novelty_check.md`
- Create: `agents/phd.md`
- Create: `agents/postdoc.md`
- Create: `agents/ml_engineer.md`
- Create: `agents/experiment_manager.md`
- Create: `agents/writing.md`
- Create: `agents/reviewer.md`
- Create: `agents/judge.md`

Each agent prompt includes: role definition, available tools, inputs it receives, outputs it must produce, quality criteria, and references to .ai/ docs it should read.

- [ ] **Step 1: Create clarification.md** — Phase 0 Q&A agent
- [ ] **Step 2: Create novelty_check.md** — Semantic Scholar gap analysis
- [ ] **Step 3: Create phd.md** — Literature survey + hypothesis generation
- [ ] **Step 4: Create postdoc.md** — Hypothesis critique + statistics
- [ ] **Step 5: Create ml_engineer.md** — Code implementation + experiments
- [ ] **Step 6: Create experiment_manager.md** — Tree search orchestration
- [ ] **Step 7: Create writing.md** — Paper writing + revision
- [ ] **Step 8: Create reviewer.md** — Peer review with 3 personas
- [ ] **Step 9: Create judge.md** — Quality gate evaluation
- [ ] **Step 10: Commit**

```bash
git add agents/
git commit -m "feat: add all 9 agent role prompt templates"
```

---

## Chunk 3: Pipeline Orchestrator

### Task 8: Stage runner — dispatches agents per stage

**Files:**
- Create: `src/stage_runner.py`

- [ ] **Step 1: Create stage_runner.py**

`StageRunner` class with methods for each stage: `run_p0()`, `run_s0()` through `run_s8()`. Each method: loads the agent prompt, prepares context from .ai/ and prior outputs, dispatches the agent (via Claude Code subprocess or API call), collects outputs, runs judge gate.

- [ ] **Step 2: Commit**

```bash
git add src/stage_runner.py
git commit -m "feat: add stage runner for dispatching agents per pipeline stage"
```

---

### Task 9: Main orchestrator — pipeline loop

**Files:**
- Create: `src/orchestrator.py`

- [ ] **Step 1: Create orchestrator.py**

`ResearchOrchestrator` class: reads registry.yaml, determines current stage, calls StageRunner for that stage, handles judge gate pass/fail (retry on fail, advance on pass), updates registry. Supports resuming from any stage.

- [ ] **Step 2: Commit**

```bash
git add src/orchestrator.py
git commit -m "feat: add main research pipeline orchestrator"
```

---

### Task 10: CLI entry point

**Files:**
- Create: `run.py`

- [ ] **Step 1: Create run.py**

CLI with subcommands:
- `python run.py start` — begin from Phase 0 (direction alignment)
- `python run.py resume` — resume from current stage in registry
- `python run.py status` — show pipeline status
- `python run.py reset <stage>` — reset a stage to pending

- [ ] **Step 2: Commit**

```bash
git add run.py
git commit -m "feat: add CLI entry point for research pipeline"
```

---

## Chunk 4: Knowledge Layer and Templates

### Task 11: .ai/ knowledge layer (research-adapted)

**Files:**
- Create: `.ai/_loading-rules.md`
- Create: `.ai/_maintenance-rules.md`
- Create: `.ai/core/architecture.md`
- Create: `.ai/core/research-context.md` (template)
- Create: `.ai/core/methodology.md` (template)
- Create: `.ai/core/literature.md` (template)
- Create: `.ai/evolution/decisions.md` (template)
- Create: `.ai/evolution/negative-results.md` (template)
- Create: `.ai/evolution/experiment-log.md` (template)

- [ ] **Step 1: Create _loading-rules.md** — research-specific decision tree (which agent loads which docs)
- [ ] **Step 2: Create _maintenance-rules.md** — research-specific triggers
- [ ] **Step 3: Create core/architecture.md** — harness architecture description
- [ ] **Step 4: Create core/ template files** — research-context, methodology, literature (placeholder for S0 to populate)
- [ ] **Step 5: Create evolution/ template files** — decisions, negative-results, experiment-log
- [ ] **Step 6: Commit**

```bash
git add .ai/
git commit -m "feat: add .ai/ research knowledge layer"
```

---

### Task 12: Output document templates

**Files:**
- Create: `templates/RESEARCH_PROPOSAL.md`
- Create: `templates/RELATED_WORK.md`
- Create: `templates/BASELINES.md`
- Create: `templates/EXPERIMENT_PLAN.md`
- Create: `templates/RESULTS_SUMMARY.md`

- [ ] **Step 1: Create all 5 templates** with section headers matching briefing specs
- [ ] **Step 2: Commit**

```bash
git add templates/
git commit -m "feat: add output document templates"
```

---

### Task 13: CLAUDE.md entry point

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md** — project identity, knowledge index table, loading/maintenance protocol, research pipeline rules

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: add CLAUDE.md entry point for research pipeline"
```

---

## Chunk 5: Integration

### Task 14: .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore** with: `__pycache__/`, `*.pyc`, `.env`, `results/`, `DELIVERY/`, `paper/*.aux` etc.

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "feat: add .gitignore"
```
