# InfiEpisteme

Automated research pipeline driven by Claude Code. Given a research direction, autonomously delivers: peer-review-quality paper (PDF), clean code repository, and organized experimental results.

## Knowledge Base (.ai/)

Before starting any task, read the relevant documents from `.ai/`.

| Document | Description |
|----------|-------------|
| .ai/_loading-rules.md | Research-specific decision tree for which docs to load per agent role |
| .ai/_maintenance-rules.md | Research-specific maintenance triggers and protocol |
| .ai/core/architecture.md | System architecture of the research pipeline harness |
| .ai/core/research-context.md | Current research question, hypothesis, success criteria |
| .ai/core/methodology.md | Proposed method and current best implementation |
| .ai/core/literature.md | Key papers, baselines, known results |
| .ai/evolution/decisions.md | All major decisions in ADR format (append-only) |
| .ai/evolution/negative-results.md | Failed experiments — prevents repeating mistakes |
| .ai/evolution/experiment-log.md | Brief log of every experiment run |
| .ai/context_chain.md | Running reasoning chain across stages — the "why" thread |
| skills/references/citation-verification.md | 5-step citation verification protocol |
| skills/references/agent-continuity.md | Cross-session continuity reference |
| skills/references/impl-nanogpt.md | nanoGPT patterns for custom small models (S3) |
| skills/references/impl-litgpt.md | LitGPT pretrain/finetune with 20+ architectures (S3/S4) |
| skills/references/impl-torchtitan.md | TorchTitan for large-scale distributed pretraining (S4) |
| skills/references/impl-fsdp2.md | PyTorch FSDP2 distributed training (S3/S4) |
| skills/references/impl-unsloth.md | Unsloth 2-5x faster LoRA training (S3/S4) |
| skills/references/impl-trl-grpo.md | GRPO/RL training with TRL (S4) |
| skills/references/impl-trl.md | TRL fine-tuning: SFT, DPO, PPO, GRPO (S4) |
| skills/references/impl-lm-eval.md | lm-evaluation-harness for benchmarking (S5) |
| skills/references/writing-guide.md | ML paper writing best practices (S6) |
| skills/references/reviewer-guidelines.md | Reviewer criteria and rebuttal strategy (S7) |
| templates/checklists/*.md | Venue-specific submission checklists (NeurIPS, ICML, ICLR, ACL, generic) |

## Loading Protocol

1. Always read this file (auto-loaded by Claude Code)
2. Read `.ai/_loading-rules.md` and follow the agent-role decision tree
3. Do not load documents speculatively — only load what your role requires

## Maintenance Protocol

After completing significant work, follow `.ai/_maintenance-rules.md`:
- Research question refined → update `core/research-context.md`
- New papers found → update `core/literature.md`
- Methodology changed → update `core/methodology.md`
- Major decision made → append to `evolution/decisions.md`
- Experiment failed → append to `evolution/negative-results.md`
- Experiment completed → append to `evolution/experiment-log.md`

## Pipeline Stages

```
[Hardware Detection] → P0: Direction Alignment (user present, ~30min)
S0: Init → S1: Literature → S2: Ideation → S3: Code →
S4: Experiments (tree search) → S5: Analysis →
S6: Writing → S7: Review-Revise → S8: Delivery
```

## Architecture (v2.1 — .md-native + MCP)

```
run.sh (main loop)
  ├── claude -p "skills/S0_hardware.md" → hardware detection (first run only)
  ├── scripts/parse_state.py → determine current stage
  ├── claude -p "skills/S{N}.md" → execute stage (MCP-first, Python fallback)
  ├── scripts/state_guard.py verify → verify outputs exist
  ├── claude -p "skills/memory_sync.md" → memory consolidation (.ai/ updates)
  ├── scripts/state_guard.py verify → verify memory quality
  ├── claude -p "skills/judge.md" → 3-layer review (deterministic → content → first-principles)
  └── scripts/state_guard.py advance → advance or retry
```

- **skills/** — 18 .md skill files + reference files, executed natively by Claude Code
- **MCP servers** — Semantic Scholar, System Monitor, SSH (Python scripts as fallback)
- **scripts/** — minimal Python CLI tools (state_guard, GPU, cross-review, scholarly)
- **state/** — runtime state files (JSON) + hardware_profile.json
- **templates/checklists/** — venue-specific submission checklists (NeurIPS, ICML, ICLR, ACL, generic)
- **PIPELINE.md** — state machine definition (expected outputs and judge criteria per stage)

## Working Principle

Use first-principles thinking. Do not assume I always know exactly what I want or how to get it. Stay careful and reason from the underlying need and the actual problem. When my motivation or goal is unclear, pause and discuss it with me. When the goal is clear but the path is not the shortest or most effective, point that out and suggest a better approach.

## Rules

1. Every skill reads .ai/ before working. The Memory Synthesizer updates .ai/ after each stage.
2. Commit knowledge updates separately: `docs(.ai): <summary>`
3. Every failed experiment goes to `evolution/negative-results.md`
4. Every figure must pass VLM review before paper inclusion
5. Judge gate (3-layer: deterministic → content quality → first-principles) must pass before advancing
6. Anti-hallucination: every citation verified via 5-step protocol (see `skills/references/citation-verification.md`)
7. State Guardian (`scripts/state_guard.py`) validates state after every skill execution
8. Cross-model adversarial review in S7 (Claude writes, external model reviews)
9. Hardware detection: `S0_hardware.md` → `hardware_profile.json`; all skills adapt to hardware
10. MCP-first: prefer MCP tools over Python scripts; scripts are fallbacks
11. Git pre-registration: experiment design committed before execution (`research(protocol):`)
12. Venue checklists: S8 verifies paper against venue-specific requirements

## Quick Reference

- Start: `./run.sh start`
- Resume: `./run.sh resume`
- Status: `./run.sh status`
- Reset: `./run.sh reset <stage>`
