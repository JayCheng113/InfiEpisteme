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
P0: Direction Alignment (user present, ~30min)
S0: Init → S1: Literature → S2: Ideation → S3: Code →
S4: Experiments (tree search) → S5: Analysis →
S6: Writing → S7: Review-Revise → S8: Delivery
```

## Architecture (v2 — .md-native)

```
run.sh (主循环)
  ├── scripts/parse_state.py → 确定当前 stage
  ├── claude -p "skills/S{N}.md" → 执行 stage（产出文件）
  ├── scripts/state_guard.py verify → 验证输出存在
  ├── claude -p "skills/memory_sync.md" → 记忆整合（.ai/ 更新）
  ├── scripts/state_guard.py verify → 验证记忆质量
  ├── claude -p "skills/judge.md" → LLM-as-judge 质量门控
  └── scripts/state_guard.py advance → 推进/重试
```

- **skills/** — 16 个 .md skill 文件，Claude Code native 执行
- **scripts/** — 极简 Python CLI 工具（state_guard, GPU, cross-review, scholarly）
- **state/** — 运行时状态文件（JSON）
- **PIPELINE.md** — 状态机定义（每 stage 的预期输出和 judge 标准）

## Rules

1. Every skill reads .ai/ before working, updates .ai/ after completing work
2. Commit knowledge updates separately: `docs(.ai): <summary>`
3. Every failed experiment goes to `evolution/negative-results.md`
4. Every figure must pass VLM review before paper inclusion
5. Judge gate must pass before advancing to the next stage
6. Anti-hallucination: every citation must be verifiable via Semantic Scholar/DBLP
7. State Guardian (`scripts/state_guard.py`) validates state after every skill execution
8. Cross-model adversarial review in S7 (Claude writes, external model reviews)

## Quick Reference

- Start: `./run.sh start`
- Resume: `./run.sh resume`
- Status: `./run.sh status`
- Reset: `./run.sh reset <stage>`
