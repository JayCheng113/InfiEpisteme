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
run.sh (主循环)
  ├── claude -p "skills/S0_hardware.md" → 硬件检测（首次运行）
  ├── scripts/parse_state.py → 确定当前 stage
  ├── claude -p "skills/S{N}.md" → 执行 stage（MCP 优先，Python fallback）
  ├── scripts/state_guard.py verify → 验证输出存在
  ├── claude -p "skills/memory_sync.md" → 记忆整合（.ai/ 更新）
  ├── scripts/state_guard.py verify → 验证记忆质量
  ├── claude -p "skills/judge.md" → LLM-as-judge 质量门控
  └── scripts/state_guard.py advance → 推进/重试
```

- **skills/** — 18 个 .md skill 文件 + 2 个 reference 文件，Claude Code native 执行
- **MCP servers** — Semantic Scholar、System Monitor、SSH（Python scripts 作为 fallback）
- **scripts/** — 极简 Python CLI 工具（state_guard, GPU, cross-review, scholarly）
- **state/** — 运行时状态文件（JSON）+ hardware_profile.json
- **templates/checklists/** — 会议特定提交 checklist（NeurIPS, ICML, ICLR, ACL, generic）
- **PIPELINE.md** — 状态机定义（每 stage 的预期输出和 judge 标准）

## Rules

1. Every skill reads .ai/ before working. The Memory Synthesizer updates .ai/ after each stage.
2. Commit knowledge updates separately: `docs(.ai): <summary>`
3. Every failed experiment goes to `evolution/negative-results.md`
4. Every figure must pass VLM review before paper inclusion
5. Judge gate must pass before advancing to the next stage
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
