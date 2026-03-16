# InfiEpisteme

Fully automated research pipeline driven by Claude Code. From a research direction to a peer-review-quality paper, code repository, and experimental results — without human intervention after kickoff.

**v2.1**: MCP integration (Semantic Scholar, System Monitor, SSH), hardware-aware experiments, 5-step citation verification, venue-specific submission checklists, Git pre-registration protocol.

## How It Works

```
You (30 min)                          Unattended (~hours)
     |                                      |
     v                                      v
  Phase 0                            Phase 1 (sleep mode)
  Direction                    S0 Init
  Alignment        ->          S1 Literature Survey (20+ papers)
  - What interests you?        S2 Ideation (6-perspective debate)
  - What's the gap?            S3 Code Implementation
  - What resources?            S4 Experiments (tree search, GPU)
                               S5 Statistical Analysis
                               S6 Paper Writing (LaTeX -> PDF)
                               S7 Review-Revise (cross-model)
                               S8 Delivery
                                      |
                                      v
                               DELIVERY/
                                 paper.pdf
                                 code/
                                 results/
```

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/your-org/InfiEpisteme.git
cd InfiEpisteme
pip install pyyaml requests

# 2. (Optional) Install MCP servers for enhanced capabilities
claude mcp add semantic-scholar -- npx -y @anthropic/mcp-semantic-scholar
claude mcp add system-monitor -- npx -y @huhabla/mcp-system-monitor
claude mcp add ssh -- npx -y @anthropic/mcp-ssh-server  # only if using remote GPU

# 3. Edit config.yaml
#    - Set research_direction
#    - Set compute budget (GPU hours, type)
#    - Set cross_review API key (optional, for adversarial review)
#    - Configure MCP settings (mcp section)

# 4. Run
./run.sh start      # Hardware detect → Interactive Phase 0 → fully unattended
./run.sh status     # Check progress anytime
./run.sh resume     # Resume after interruption
./run.sh reset S4   # Reset a stage and retry
```

## Architecture

**.md files are the program.** All research logic lives in `skills/*.md` files that Claude Code executes natively. Python is used only for things markdown genuinely cannot do.

```
run.sh (bash loop)
  |
  +--> claude -p "skills/S0_hardware.md"                  # Hardware detection (once)
  +--> claude -p "skills/_common.md + skills/S{N}.md"     # Execute stage (MCP-first)
  +--> scripts/state_guard.py verify                      # Validate state
  +--> claude -p "skills/memory_sync.md"                  # Consolidate knowledge
  +--> scripts/state_guard.py verify                      # Validate memory
  +--> claude -p "skills/judge.md"                        # Quality gate
  +--> scripts/state_guard.py advance                     # Progress pipeline
```

### Why .md-native?

Inspired by [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) and [Sibyl](https://github.com/Sibyl-Research-Team/sibyl-research-system), we found that structured markdown is all an LLM needs to execute complex workflows. No framework overhead, no hidden state, fully auditable — every decision the agent makes traces back to a readable `.md` file.

## Project Structure

```
InfiEpisteme/
|-- run.sh                   # Pipeline driver (bash)
|-- PIPELINE.md              # State machine: stages, criteria, transitions
|-- config.yaml              # Your settings (compute, APIs, preferences)
|-- registry.yaml            # Pipeline state (managed by scripts)
|-- experiment_tree.json     # Experiment search tree
|
|-- skills/                  # The program (18 .md skill files + references)
|   |-- _common.md           # Shared preamble (MCP fallback, hardware, anti-hallucination)
|   |-- S0_hardware.md       # Hardware detection → hardware_profile.json
|   |-- P0_clarification.md  # Phase 0: research direction interview
|   |-- P0_novelty.md        # Phase 0: novelty check (Semantic Scholar MCP)
|   |-- S0_init.md           # Bootstrap .ai/ knowledge base
|   |-- S1_literature.md     # Multi-source literature survey (MCP-first)
|   |-- S2_ideation.md       # 6-perspective hypothesis debate (hardware-aware)
|   |-- S3_implementation.md # Code baselines + proposed methods (hardware-aware)
|   |-- S4_experiments.md    # Progressive tree search (SSH MCP, Git pre-registration)
|   |-- S4_run_node.md       # Single experiment execution (SSH MCP, hardware-aware)
|   |-- S5_analysis.md       # 6-perspective statistical analysis
|   |-- S6_writing.md        # LaTeX paper (5-step citation verification)
|   |-- S7_review.md         # Cross-model adversarial review
|   |-- S7_revise.md         # Address reviewer feedback
|   |-- S8_delivery.md       # Package deliverables + venue checklist
|   |-- judge.md             # LLM-as-judge quality gate
|   |-- memory_sync.md       # Memory Synthesizer (.ai/ consolidation)
|   |-- vlm_review.md        # VLM figure quality review
|   +-- references/          # Reference documents
|       |-- citation-verification.md  # 5-step citation protocol
|       +-- agent-continuity.md       # Cross-session continuity
|
|-- scripts/                 # Minimal Python CLI tools
|   |-- state_guard.py       # State validation + repair after each skill
|   |-- gpu_submit.py        # GPU job submission (local / SLURM)
|   |-- gpu_poll.py          # GPU job monitoring
|   |-- cross_review.py      # External model review dispatch
|   |-- scholarly_search.py  # Semantic Scholar API client
|   |-- parse_state.py       # Read registry.yaml
|   +-- update_state.py      # Update registry.yaml
|
|-- .ai/                     # Persistent knowledge layer (AgentInfra)
|   |-- core/                # Research context, methodology, literature
|   +-- evolution/           # Decisions, negative results, experiment log
|
|-- templates/               # Output document + LaTeX templates
|   |-- checklists/          # Venue-specific submission checklists
|   |   |-- neurips.md       # NeurIPS checklist (16 items)
|   |   |-- icml.md          # ICML reproducibility checklist
|   |   |-- iclr.md          # ICLR checklist (LLM disclosure = desk reject)
|   |   |-- acl.md           # ACL checklist (Limitations required)
|   |   +-- generic.md       # Generic ML paper checklist
|   +-- latex/               # LaTeX venue templates
+-- state/                   # Runtime state files (JSON)
```

## Key Design Decisions

### Memory System (solving stateless sessions)

Each `claude -p` call is completely stateless — no conversation history. Memory is reconstructed from files via a three-layer architecture:

```
Layer 1: State (YAML/JSON)          — registry.yaml, experiment_tree.json
Layer 2: Knowledge (.ai/ markdown)  — distilled summaries, decisions, negative results
Layer 3: Context Chain              — .ai/context_chain.md: the "why" thread across stages
```

**Key innovation**: Executing skills do NOT update `.ai/` files. A dedicated **Memory Synthesizer** (`skills/memory_sync.md`) runs after every stage to read outputs and consolidate knowledge. This separation of concerns ensures memory quality — inspired by [Google's Always On Memory Agent](https://github.com/nicholasgoulet/memory-agent) consolidation pattern.

The pipeline loop is: `execute → verify → memory_sync → verify_memory → judge → advance`

### State Guardian

`scripts/state_guard.py` runs after every skill to verify and repair state:

- Expected output files exist?
- `registry.yaml` fields correctly updated?
- `.ai/` content quality (min length, citations present, rationale included)?
- `context_chain.md` has entry for current stage?

Deterministic Python, not LLM — complements the LLM-as-judge content quality checks.

### Cross-Model Adversarial Review

In Stage S7, the paper written by Claude is reviewed by an external model (GPT-4o by default). This eliminates the single-model self-review blind spot identified by [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep):

| Reviewer | Model | Focus |
|----------|-------|-------|
| R1 | External (GPT-4o) | Methods, technical soundness |
| R2 | Internal (Claude) | Clarity, presentation |
| R3 | External (GPT-4o) | Novelty, contribution |

Configure in `config.yaml` under `cross_review`.

### Multi-Perspective Debate

Adapted from [Sibyl Research System](https://github.com/Sibyl-Research-Team/sibyl-research-system):

**Ideation (S2)** — 6 perspectives generate and critique hypotheses:
Innovator, Pragmatist, Theorist, Contrarian, Interdisciplinary, Empiricist

**Analysis (S5)** — 6 perspectives interpret results:
Optimist, Skeptic, Strategist, Methodologist, Comparativist, Revisionist

### Progressive Experiment Tree Search

Stage S4 doesn't run one experiment — it searches:

```
Stage 4.1: Preliminary (6 root nodes, 3 per hypothesis)
    |  select best per hypothesis
    v
Stage 4.2: Hyperparameter tuning (3 variants per winner)
    |  select best
    v
Stage 4.3: Method refinement (3 architectural variants)
    |  select best
    v
Stage 4.4: Ablation studies (remove each component)
    |
    v
  RESULTS_SUMMARY.md
```

### MCP Integration (v2.1)

Three core MCP servers replace Python scripts as the primary tool interface:

| MCP Server | Purpose | Fallback |
|------------|---------|----------|
| **Semantic Scholar** | Paper search, details, citation retrieval | `scripts/scholarly_search.py` |
| **System Monitor** | CPU/GPU/RAM/disk detection | `nvidia-smi`, `psutil` |
| **SSH** | Remote GPU job submission and polling | `scripts/gpu_submit.py` |

All MCP tools are optional — Python scripts serve as automatic fallbacks. Configure in `config.yaml` under the `mcp` section.

### Hardware-Aware Experiments (v2.1)

At pipeline start, `skills/S0_hardware.md` detects hardware and writes `hardware_profile.json`. All downstream skills adapt:

- **S2 Ideation**: Only proposes feasible hypotheses for available hardware
- **S3 Implementation**: Chooses DDP/FSDP vs single-GPU based on GPU count
- **S4 Experiments**: Sets batch sizes and parallelism from VRAM and GPU count
- No GPU? Skills flag for SSH remote execution or CPU-only alternatives.

### Citation Verification (5-Step Protocol)

Adapted from [Orchestra Research](https://github.com/orchestra-research/ai-research-skills):

1. **Search** — Find paper via Semantic Scholar MCP
2. **Verify** — Confirm in 2+ independent sources (Semantic Scholar + arXiv/CrossRef)
3. **Retrieve** — Get BibTeX from authoritative source (never from LLM memory)
4. **Validate** — Check paper content supports your citation claim
5. **Add** — Use consistent key format: `author_year_firstword`

### Git Pre-Registration

Experiment designs are committed before execution, creating a lightweight pre-registration:

```
research(protocol): H1 — attention-based fusion     # committed before running
research(results): H1_R1 — accuracy=0.847           # committed after results
research(reflect): pivot to H2 — H1 ceiling reached # outer-loop decisions
```

### Anti-Hallucination

Every citation in the paper must pass the 5-step verification protocol. The `_common.md` preamble enforces this as a non-negotiable rule across all skills. See `skills/references/citation-verification.md`.

### Venue-Specific Checklists (v2.1)

Before delivery, S8 verifies the paper against venue-specific requirements:

- **NeurIPS**: Broader Impacts, LLM disclosure, reproducibility (16 items)
- **ICML**: Statistical reporting, reproducibility checklist
- **ICLR**: LLM usage statement (missing = desk rejection)
- **ACL**: Limitations section (required), bias/fairness
- **Generic**: Standard ML paper quality checks

## Safety Mechanisms

| Mechanism | Purpose |
|-----------|---------|
| **Circuit breaker** | Same failure 3x in a row -> pipeline pauses, alerts user |
| **Max review cycles** | 4 cycles max (prevents infinite review loops) |
| **GPU budget check** | Experiments >4 GPU-hours flagged before submission |
| **Judge gate** | Every stage must pass LLM-as-judge before advancing |
| **State persistence** | `registry.yaml` + git commits enable resume from any point |
| **Idempotent skills** | Skills check existing outputs before redoing work |
| **Hardware detection** | `hardware_profile.json` prevents experiments exceeding resources |
| **Citation verification** | 5-step protocol eliminates ~40% LLM citation error rate |
| **Git pre-registration** | Experiment design committed before execution |
| **Venue checklists** | Venue-specific requirements checked before delivery |

## Configuration

Edit `config.yaml`:

```yaml
research_direction: "your research question here"
target_venue: "NeurIPS 2026"        # or "ICML 2026", "arxiv"
target_score: 6.0                    # minimum reviewer score

compute:
  gpu_hours: 100
  gpu_type: "A100"
  parallel_jobs: 3

mcp:
  semantic_scholar: true       # Semantic Scholar MCP (fallback: scholarly_search.py)
  system_monitor: true         # System Monitor MCP (fallback: nvidia-smi)
  ssh_remote: false            # SSH MCP for remote GPU (fallback: gpu_submit.py)
  ssh_host: ""                 # SSH target host

cross_review:
  enabled: true
  model: "gpt-4o"
  api_key_env: "OPENAI_API_KEY"      # environment variable name

resources:
  semantic_scholar_key: ""           # optional, for higher API throughput
```

## What It Produces

```
DELIVERY/
  paper.pdf                   # Peer-review-quality paper
  code/
    src/                      # Clean implementation
    README_code.md            # Reproduction instructions
    requirements.txt
  results/
    experiment_tree.json      # Full search tree with scores
    {winning_node}/
      metrics.json
      figures/
  reviews/
    cycle_1/, cycle_2/, ...   # All reviewer feedback
  DELIVERY.md                 # Summary for human
```

## Acknowledgments

Design informed by:
- [ARIS (Auto-Research-In-Sleep)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) — adversarial cross-model review, state-persistent review loops, modular skills
- [Sibyl Research System](https://github.com/Sibyl-Research-Team/sibyl-research-system) — multi-perspective debate, stateless-with-artifacts architecture, self-healing
- [GPT-Researcher](https://github.com/assafelovic/gpt-researcher) — multi-source aggregation, recursive tree exploration
- [AgentInfra](https://github.com/JayCheng113/AgentInfra) — .ai/ persistent knowledge layer convention
- [Orchestra Research](https://github.com/orchestra-research/ai-research-skills) — 5-step citation verification, venue checklists, Git pre-registration protocol

## License

MIT
