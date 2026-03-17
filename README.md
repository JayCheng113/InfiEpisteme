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

The most effective way to run InfiEpisteme is **talking to your local Claude Code** and letting it supervise the remote pipeline. You don't need to write SSH commands or remember script arguments — just have a conversation.

### Why Supervise Instead of Fire-and-Forget?

For **cutting-edge topics** (papers released days ago, novel combinations), the pipeline will hit problems that need real-time judgment. Local CC catches these within minutes instead of discovering them after 3 failed retries.

### Conversation Template

Below is a real conversation flow from our first supervised run (studying Kimi's Attention Residuals, a paper released 2 days prior). Copy this pattern:

---

**Phase 0: Setup & Direction**

```
You: My server is ubuntu@129.146.162.231 with an A100.
     Clone InfiEpisteme and set it up there.

CC:  [SSHs to server, clones repo, checks hardware]
     Done. A100-40GB, 216GB RAM, CUDA 12.8.
     What's your research direction?

You: Study Kimi's recently proposed Attention Residuals, validate
     performance on 3B LLMs, and propose improvements.
     Target NeurIPS 2026. Use gpt-5.4 for cross_review.

CC:  [searches web for AttnRes paper — finds arxiv:2603.15031, 2 days old]
     [identifies 5 competing methods: DCA, MUDDFormer, Hyper-Connections...]
     [writes config.yaml and RESEARCH_PROPOSAL.md on server]

     Risk warnings:
     1. Paper released only 2 days ago — Semantic Scholar likely hasn't indexed it
     2. S1's 30-paper requirement needs broadening to residual connections field
     3. 0.5B model is more realistic — 80 GPU-hours only allows ~6 training runs

You: A small-scale validation is fine. 0.5B or 1.5B, your call.

CC:  [adjusts proposal to 0.5B scale, 5-10B tokens per run]
     [executes P0 novelty check — finds direction is "Partially Novel"]
     P0 complete, advancing to S0.
```

**Phase 1: Supervised Execution**

```
CC:  [executes S0 init, S1 literature survey on server]
     S1 finished but state guard reports error: only detected 21 citations, need 30.

     Diagnosis: citations use [Author et al., 2024] format, but state_guard.py
     regex doesn't match the dot in "et al."

     [fixes regex locally, pushes to GitHub, syncs to server]
     [runs supplementary search to add 15 more papers]
     Re-verified: 6/6 checks passed. Advancing to S2.

You: Did you push the local fix?

CC:  Already pushed (commit 27d15fe).
```

**Phase 2: Ongoing Monitoring**

```
You: What's the status?

CC:  [checks registry.yaml on server]
     S2 Ideation complete. Generated 2 hypotheses, 6 experiment nodes.
     S3 Implementation is running...

You: Watch GPU memory during S4. 0.5B with bf16 should fit.

CC:  Got it. I'll check hardware_profile.json before S4 starts
     and ensure batch sizes are reasonable.

     ...

CC:  S4.1 done, 3/6 nodes succeeded. One OOM'd —
     batch_size=64 too large. Already changed to 32 and rerunning.
```

**Phase 3: Intervention**

```
You: I looked at the results, H2's direction seems wrong. Can you change it to...?

CC:  [reads experiment_tree.json, updates H2 nodes]
     [resets S4 judge result, re-runs affected sub-stage]
     Adjusted. New direction nodes committed.

You: The paper has too few citations and nothing recent.

CC:  [diagnoses: S6 only cited 21 papers, no 2025-2026 papers]
     [adds citation count enforcement to state_guard.py]
     [runs targeted supplement search for recent papers]
     Fixed and pushed.
```

### Risk Prediction Checklist

Before each stage, tell CC to watch for these:

| Stage | Risk Signal | What to Tell CC |
|-------|------------|-----------------|
| **S1** | Paper < 6 months old | "This paper is very new, Semantic Scholar may not have it. Use WebSearch as fallback." |
| **S1** | Niche topic | "Not many papers in this area. May not reach 30 — broaden to related fields." |
| **S2** | Limited hardware | "Make sure experiments fit within 80 GPU-hours budget." |
| **S3** | No reference code | "Original paper has no open-source code. S3 may need to implement from scratch." |
| **S4** | Budget overrun | "Monitor GPU usage. Stop early if approaching budget." |
| **S6** | Citation issues | "Check citation count and format. We had a regex mismatch bug before." |
| **S7** | API key missing | "Confirm OPENAI_API_KEY is set, or cross-review will fail." |

### Key Phrases for CC

| You Say | CC Does |
|---------|---------|
| "Run the pipeline on the server" | SSH to server, configure, start execution |
| "What's the status?" | Reads registry.yaml, reports current stage and progress |
| "What are the risks for this stage?" | Analyzes research topic vs pipeline requirements, flags issues |
| "Did you push the fix?" | Checks git status, commits, pushes to GitHub |
| "Stop, I want to change direction" | Kills processes, resets stage, waits for new instructions |
| "Continue" | Resumes from current stage |
| "Sync local fixes to server" | rsync updated files or git pull on server |

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
