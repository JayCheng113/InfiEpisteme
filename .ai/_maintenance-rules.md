---
name: Maintenance Rules
description: Research-specific protocol for when and how to update .ai/ knowledge documents
---

# Knowledge Maintenance Protocol — Research Pipeline

## Mandatory Triggers

1. **Research question refined** → Update `core/research-context.md`
2. **New papers found** → Update `core/literature.md`
3. **Methodology changed** → Update `core/methodology.md`
4. **Major decision made** → Append to `evolution/decisions.md` (ADR format)
5. **Experiment failed** → Append to `evolution/negative-results.md`
6. **Experiment completed** → Append to `evolution/experiment-log.md`

## Agent-Specific Responsibilities

| Agent | Must Update |
|-------|-------------|
| Clarification | research-context.md |
| Novelty Check | literature.md |
| PhD | literature.md, methodology.md, decisions.md |
| Postdoc | methodology.md, decisions.md |
| ML Engineer | experiment-log.md, negative-results.md |
| Experiment Manager | experiment-log.md, negative-results.md |
| Writing | (reads only — no updates) |
| Reviewer | (reads only — no updates) |

## Commit Protocol

- Knowledge updates committed separately: `docs(.ai): <summary>`
- Never mix .ai/ updates with code changes in the same commit

## Critical: Negative Results

`.ai/evolution/negative-results.md` is the most important document for preventing wasted work. Every failed experiment MUST record:
- What was tried
- What happened
- Why it failed (hypothesis)
- What this means for future attempts
