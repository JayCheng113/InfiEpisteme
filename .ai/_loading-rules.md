---
name: Loading Rules
description: Research-specific decision tree for which .ai/ documents to load based on agent role and pipeline stage
---

# Loading Decision Rules — Research Pipeline

## Overview

These rules guide each agent in deciding which .ai/ documents to load. Each agent role has specific document needs.

## Step 1: Always Load

Every agent starts with:
1. `CLAUDE.md` (auto-loaded)
2. `.ai/core/research-context.md` — current research question and hypothesis
3. `.ai/context_chain.md` — reasoning chain across stages (read the last 2-3 entries for recent context)

## Step 2: Load by Agent Role

### Clarification Agent (P0)
- Load nothing extra — starting fresh

### Novelty Check Agent (P0)
- `.ai/core/literature.md` (if exists)

### PhD Agent (S1, S2)
- `.ai/core/literature.md`
- `.ai/core/methodology.md`
- `.ai/evolution/decisions.md`

### Postdoc Agent (S2, S5)
- `.ai/core/methodology.md`
- `.ai/core/literature.md`
- `.ai/evolution/negative-results.md`

### ML Engineer Agent (S3, S4)
- `.ai/core/methodology.md`
- `.ai/evolution/negative-results.md`
- `.ai/evolution/experiment-log.md`

### Experiment Manager Agent (S4)
- `.ai/core/methodology.md`
- `.ai/evolution/experiment-log.md`
- `.ai/evolution/negative-results.md`

### Writing Agent (S6, S7)
- `.ai/core/research-context.md`
- `.ai/core/methodology.md`
- `.ai/core/literature.md`
- `.ai/evolution/decisions.md`

### Reviewer Agent (S7)
- `.ai/core/research-context.md` (only — reviewers should approach the paper fresh)

### Judge Agent (all stages)
- Load only the stage-specific outputs being evaluated

### Memory Synthesizer (runs after every stage)
- ALL `.ai/core/` and `.ai/evolution/` files
- Stage output files (to distill into .ai/)
- `.ai/context_chain.md` (to append new entry)

## Step 3: Load Implementation References (skills/references/)

These reference files contain framework-specific code patterns from [Orchestra Research](https://github.com/Orchestra-Research/AI-Research-SKILLs). Load them **on demand via the Read tool** — do NOT skip this step.

### S3 (Implementation) — MUST load at least one:
| Condition | Reference to Read |
|-----------|-------------------|
| Building custom model < 1B params | `skills/references/impl-nanogpt.md` |
| Using existing architecture (LLaMA, Mistral, Qwen) | `skills/references/impl-litgpt.md` |
| `hardware_profile.json` shows GPU count > 1 | `skills/references/impl-fsdp2.md` |
| `hardware_profile.json` shows VRAM < 24GB | `skills/references/impl-unsloth.md` |

### S4 (Experiments) — Load based on experiment type:
| Condition | Reference to Read |
|-----------|-------------------|
| Standard pretraining experiments | `skills/references/impl-nanogpt.md` or `impl-litgpt.md` |
| `config.yaml` research_direction mentions GRPO/alignment/RL | `skills/references/impl-trl-grpo.md` |
| Post-training (SFT, DPO, PPO) | `skills/references/impl-trl.md` |
| Multi-GPU distributed training | `skills/references/impl-torchtitan.md` or `impl-fsdp2.md` |
| Single GPU, memory-constrained | `skills/references/impl-unsloth.md` |

### S5 (Analysis) — MUST load:
| Condition | Reference to Read |
|-----------|-------------------|
| LLM evaluation on standard benchmarks | `skills/references/impl-lm-eval.md` |

### S6 (Writing) — MUST load:
| Condition | Reference to Read |
|-----------|-------------------|
| Always | `skills/references/writing-guide.md` |
| Always | `skills/references/citation-verification.md` |

### S7 (Review) — MUST load:
| Condition | Reference to Read |
|-----------|-------------------|
| Always | `skills/references/reviewer-guidelines.md` |

## Step 4: Budget Check

- Total loaded .ai/ documents per agent: ≤ 5 (excluding context_chain.md which is always loaded)
- Reference files (skills/references/) do NOT count toward this budget — load as many as relevant
- If context is too large, prioritize: research-context > context_chain > methodology > literature
