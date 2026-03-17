# InfiEpisteme

Automated research pipeline designed for **local Claude Code remote supervision**. Clone this repo to a GPU server, then let your local Claude Code drive the entire research process — from literature review to a peer-review-quality paper — while you retain full control to steer direction at any moment.

**v2.1**: MCP integration (Semantic Scholar, System Monitor, SSH), hardware-aware experiments, 5-step citation verification, venue-specific submission checklists, Git pre-registration protocol.

## How It Works

```
Phase 0: Local (you + Claude Code)           Phase 1: Remote (unattended)
┌─────────────────────────────┐              ┌──────────────────────────┐
│  You ←→ Claude Code         │              │  Remote GPU Server       │
│                             │              │  InfiEpisteme/           │
│  "I want to study X..."    │              │                          │
│  "What about Y approach?"  │   SSH/MCP    │  run.sh start            │
│                             │─────────────→│    S0 Init               │
│  Claude Code:               │              │    S1 Literature (20+)   │
│  - Web search arXiv/Scholar │   monitor    │    S2 Ideation (debate)  │
│  - Find gaps in literature  │←─────────────│    S3 Implementation     │
│  - Challenge your ideas     │              │    S4 Experiments (GPU)  │
│  - Refine research question │   intervene  │    S5 Analysis           │
│                             │─────────────→│    S6 Paper (LaTeX)      │
│  Output: config.yaml +      │              │    S7 Review-Revise      │
│          RESEARCH_PROPOSAL.md│              │    S8 Delivery           │
│                             │              │         ↓                │
│  "Looks good. Go run it."  │              │    DELIVERY/             │
│                             │              │      paper.pdf           │
│  (you can intervene anytime │              │      code/               │
│   during Phase 1 too)       │              │      results/            │
└─────────────────────────────┘              └──────────────────────────┘
```

**Phase 0 happens locally** — you and Claude Code brainstorm the research direction in a live conversation. Claude Code searches the web for recent papers, identifies gaps, and challenges your assumptions. This is far richer than filling in a `config.yaml` and pressing start. When you're satisfied with the direction, Claude Code writes the proposal, SSHs to the remote server, and kicks off the unattended pipeline.

**Phase 1 runs remotely** — the GPU server executes S0 through S8 autonomously. But your local Claude Code stays connected as the supervisor:

- **Self-healing.** If S4 (experiments) fails due to OOM, Claude Code reads the remote logs, diagnoses the issue, fixes the config, and re-runs — without waking you up.
- **Human-in-the-loop.** You can check in anytime. "How's it going?" → Claude Code reads `registry.yaml` remotely and reports status. "Change the learning rate range" → Claude Code SSHs in and adjusts.
- **Web-augmented.** Mid-pipeline, you find a relevant new paper? Claude Code searches the web for it, reads it, and updates the remote `.ai/core/literature.md` and experiment plan.
- **Cross-session continuity.** Walk away, come back tomorrow. Claude Code reads `.ai/` and `registry.yaml` from the remote server, reconstructs full context, and picks up exactly where things left off.

## Setup

### 1. Remote Server (one-time)

```bash
# On your GPU server
git clone https://github.com/your-org/InfiEpisteme.git
cd InfiEpisteme
pip install pyyaml requests

# Verify Claude Code is available on the server
claude --version
```

### 2. Local Machine (one-time)

```bash
# Add SSH MCP server so local Claude Code can reach the remote
claude mcp add ssh -- npx -y <ssh-mcp-package>

# Optional: add Semantic Scholar MCP for literature search
claude mcp add semantic-scholar -- npx -y <semantic-scholar-mcp-package>
```

### 3. Phase 0 — Local Brainstorm (you + Claude Code)

Start a conversation with your local Claude Code. No need to edit config files — just talk:

```
You: I'm interested in whether MLP-Mixer can match ViT on CIFAR-10
     with sub-1M parameters. What do you think?

CC:  [searches web for recent MLP-Mixer papers, training recipes]
     Interesting direction. Recent work shows training recipes matter more
     than architecture — ConvNeXt showed this for CNNs. The gap hasn't been
     systematically tested for Mixer vs ViT at small scale. Let me check
     Semantic Scholar for prior work...
     [searches] Found 3 related papers but none directly compare sub-1M.
     This looks novel. What venue are you targeting?

You: NeurIPS 2026. I have 4x A100 on my server at user@gpu-box.

CC:  Good. A few questions to sharpen the proposal:
     - Are you more interested in "which architecture wins" or
       "how much does training recipe explain"?
     - Should we include hybrid architectures (e.g., PoolFormer)?
     ...
```

When the direction is clear, Claude Code writes `config.yaml` and `RESEARCH_PROPOSAL.md`, then you greenlight:

```
You: Looks good. Go run it on the server.

CC:  [SSHs to user@gpu-box:~/InfiEpisteme]
     [writes config.yaml, commits RESEARCH_PROPOSAL.md]
     [runs ./run.sh start --skip-p0]
     Pipeline started. S0 (init) running now. I'll monitor progress
     and report back at each stage. ETA for S1 (literature): ~20 min.
```

### 4. Phase 1 — Remote Execution (unattended, supervised)

The pipeline runs autonomously on the server. Your local Claude Code monitors via SSH and intervenes when needed:

```
CC:  [periodic check] S1 complete — found 24 papers, 4 baselines identified.
     S2 (ideation) starting. I'll let you know when hypotheses are ready.

     ...

CC:  S2 generated 3 hypotheses. Want to review before experiments begin?

You: Show me.

CC:  [reads remote EXPERIMENT_PLAN.md via SSH]
     H1: Modern training recipe closes 80% of Mixer-ViT gap
     H2: Token-mixing MLP is the bottleneck — replacing it with pooling helps
     H3: Mixer benefits more from data augmentation than ViT

You: H2 is interesting. Drop H3, add a hypothesis about patch size sensitivity.

CC:  [SSHs in, updates EXPERIMENT_PLAN.md and experiment_tree.json]
     [resets S2 judge result, pipeline re-validates and continues to S3]
     Done. Revised plan committed. S3 (implementation) starting.
```

You can also just leave it running and check in later:

```
You: How's the research going?

CC:  [reads remote registry.yaml and experiment_tree.json]
     Currently at S4.2 (hyperparameter tuning). 2/3 nodes complete.
     Best accuracy so far: 87.2% (H1, lr=3e-4, cosine schedule).
     No failures. ETA for S4 completion: ~40 min.
```

### Pipeline Commands (via Claude Code or directly on server)

```bash
./run.sh start           # Hardware detect → Phase 0 → full pipeline
./run.sh start --skip-p0 # Skip Phase 0 (when proposal already written locally)
./run.sh status          # Check current stage and progress
./run.sh resume          # Resume after interruption
./run.sh reset S4        # Reset a stage and retry
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

## Local CC Supervision Workflow

The most effective way to run InfiEpisteme is **local Claude Code supervising a remote pipeline**. Your local CC acts as a mission controller: configuring, launching, monitoring risk, catching failures, hotfixing, and resuming — all through SSH.

### Why Not Just `./run.sh start` on the Server?

Running the pipeline unattended works for well-established research directions. But for **cutting-edge topics** (papers released days ago, novel combinations, under-explored areas), the pipeline will hit problems that require real-time judgment:

- Literature search APIs haven't indexed the target paper yet
- Citation count thresholds fail because the field is too new
- State guard regex doesn't match the citation format the LLM chose
- Experiment designs exceed hardware budget
- Judge criteria are too strict/lenient for the specific domain

Local CC supervision catches these **within minutes** instead of discovering them after 3 failed retries and a paused pipeline.

### The Workflow

```
Local Machine (Claude Code)                    Remote GPU Server
┌──────────────────────────────┐              ┌──────────────────────────┐
│                              │              │                          │
│  1. Configure & Launch       │              │                          │
│     ssh server "cd project   │──────────────│  config.yaml written     │
│     && cat > config.yaml"    │              │  registry.yaml reset     │
│                              │              │                          │
│  2. Execute Stage            │              │                          │
│     ssh server "claude -p    │──────────────│  claude -p runs skill    │
│     '$(cat skills/S{N}.md)'" │              │  produces outputs        │
│                              │              │                          │
│  3. Verify & Monitor         │              │                          │
│     ssh server "python3      │──────────────│  state_guard.py verify   │
│     scripts/state_guard.py   │              │  returns pass/fail       │
│     verify --stage S{N}"     │◄─────────────│                          │
│                              │              │                          │
│  4. Risk Detection           │              │                          │
│     "Only 21 citations,      │              │                          │
│      need 30. The regex      │              │                          │
│      doesn't match 'et al.'" │              │                          │
│                              │              │                          │
│  5. Hotfix & Retry           │              │                          │
│     Fix state_guard.py       │              │                          │
│     locally, push to GitHub, │──────────────│  rsync fixed script      │
│     rsync to server          │              │  re-verify: PASSED       │
│                              │              │                          │
│  6. Judge & Advance          │              │                          │
│     ssh server "python3      │──────────────│  advance to next stage   │
│     scripts/state_guard.py   │◄─────────────│                          │
│     advance --stage S{N}"    │              │                          │
│                              │              │                          │
│  7. Repeat from step 2       │              │                          │
└──────────────────────────────┘              └──────────────────────────┘
```

### Step-by-Step Commands

**1. Setup & Launch**
```bash
# SSH to server, configure project
ssh user@gpu-server "cd ~/project && cat > config.yaml << 'EOF'
research_direction: "your direction"
target_venue: "NeurIPS 2026"
...
EOF"

# Set stage to running
ssh user@gpu-server "cd ~/project && python3 scripts/update_state.py set_running S1"
```

**2. Execute a Stage**
```bash
# Run skill via claude -p (pipe prompt from skill files)
ssh -o ServerAliveInterval=60 user@gpu-server \
  "cd ~/project && timeout 1200 claude -p \"\$(cat skills/_common.md)
\$(cat skills/S1_literature.md)\" \
  --allowedTools 'Bash,Read,Write,Edit,Glob,Grep,WebSearch,Agent' \
  2>&1 | tee state/S1_output.log | tail -80"
```

For long-running stages, run in background:
```bash
# Use Bash tool with run_in_background=true, then check later
ssh user@gpu-server "nohup claude -p '...' > state/S4_output.log 2>&1 &"
```

**3. Verify**
```bash
ssh user@gpu-server "cd ~/project && python3 scripts/state_guard.py verify --stage S1"
# Output: Guard: 6/6 checks passed, 0 repairs, 1 warnings
```

**4. Diagnose Failures**
```bash
# Check what went wrong
ssh user@gpu-server "cd ~/project && cat state/GUARD_RESULT.json"

# Read the output files to understand the issue
ssh user@gpu-server "cd ~/project && head -40 RELATED_WORK.md"

# Count citations manually to verify
ssh user@gpu-server "cd ~/project && grep -oP '\[[A-Z][\w\s.,&]+\d{4}\]' RELATED_WORK.md | sort -u | wc -l"
```

**5. Hotfix Locally, Push, Sync**
```bash
# Fix the bug in your local repo
# Edit scripts/state_guard.py locally

# Push to GitHub
git add scripts/state_guard.py && git commit -m "fix: citation regex" && git push

# Sync to server
rsync -az scripts/state_guard.py user@gpu-server:~/project/scripts/
```

**6. Supplement & Retry**
```bash
# If outputs are insufficient, run a targeted supplement
ssh user@gpu-server "cd ~/project && timeout 600 claude -p \
  'Read RELATED_WORK.md. It has only 21 citations, need 30+. Add 10 more papers covering: ...' \
  --allowedTools 'Bash,Read,Write,Edit,WebSearch' 2>&1 | tail -20"

# Re-verify
ssh user@gpu-server "cd ~/project && python3 scripts/state_guard.py verify --stage S1"
```

**7. Judge & Advance**
```bash
# Write judge result (or run claude -p with judge.md)
ssh user@gpu-server "cd ~/project && python3 scripts/state_guard.py advance --stage S1"
# Output: PASSED — advanced to S2
```

### Risk Prediction Checklist

Before each stage, anticipate problems based on your research topic:

| Stage | Risk Signal | What to Watch |
|-------|------------|---------------|
| **S1** | Paper < 6 months old | Semantic Scholar won't have it. Use `WebSearch` fallback. Broaden to related fields for 30-paper quota. |
| **S1** | Niche topic | May not reach 30 papers. Document search queries tried; threshold can be manually lowered. |
| **S2** | Limited hardware | Check that proposed experiments fit in GPU-hours budget. 0.5B model × 5B tokens ≈ 13hrs on A100-40GB. |
| **S3** | No reference implementation | If the paper has no code release, S3 will take longer and may produce bugs. Plan for debugging time. |
| **S4** | Budget overrun | Monitor `experiment_tree.json` GPU-hours. Kill early if approaching budget. |
| **S4** | experiment_tree.json not updated | Known issue: LLM sometimes forgets to update node status. Check manually after each sub-stage. |
| **S6** | Citation format mismatch | `state_guard.py` regex must match the format S6 uses. Verify with `grep` before relying on automated checks. |
| **S7** | Cross-review API failure | If `OPENAI_API_KEY` not set or model unavailable, S7 falls back to self-review. Check logs. |

### Monitoring Commands Cheat Sheet

```bash
# Pipeline status
ssh user@gpu-server "cd ~/project && cat registry.yaml | head -15"

# Current stage output (live tail)
ssh user@gpu-server "cd ~/project && tail -50 state/S{N}_output.log"

# Last judge result
ssh user@gpu-server "cd ~/project && cat state/JUDGE_RESULT.json | python3 -m json.tool"

# GPU usage
ssh user@gpu-server "nvidia-smi"

# Experiment progress
ssh user@gpu-server "cd ~/project && python3 -c \"
import json; t=json.load(open('experiment_tree.json'))
for n in t.get('nodes',[]): print(f'{n[\"id\"]:15s} {n[\"status\"]:10s} {n.get(\"results\",{}).get(\"primary_metric\",\"\")}')
\""

# Git log (verify pre-registration)
ssh user@gpu-server "cd ~/project && git log --oneline -10"
```

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
