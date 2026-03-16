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

## Memory Synthesizer Responsibility

Individual skills do NOT update .ai/ directly. The Memory Synthesizer (`skills/memory_sync.md`) consolidates knowledge after each stage. The trigger list above documents WHAT gets updated (for memory_sync reference), but the actual writes are performed by the memory_sync skill, not by individual stage skills.

## Commit Protocol

- Knowledge updates committed separately: `docs(.ai): <summary>`
- Never mix .ai/ updates with code changes in the same commit

## Critical: Negative Results

`.ai/evolution/negative-results.md` is the most important document for preventing wasted work. Every failed experiment MUST record:
- What was tried
- What happened
- Why it failed (hypothesis)
- What this means for future attempts
