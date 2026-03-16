# Agent Continuity Reference

> Reference document for memory_sync.md and any skill dealing with cross-session state.
> Adapted from Orchestra Research `0-autoresearch-skill/references/agent-continuity.md`.

## The Problem

Each `claude -p` invocation is completely stateless — no conversation history, no memory of previous calls. The agent must reconstruct its understanding entirely from files.

## Continuity Mechanisms in InfiEpisteme

### Layer 1: Structural State (YAML/JSON)
- `registry.yaml` — pipeline position, stage status, attempt counts
- `experiment_tree.json` — experiment tree with all node states and results
- `state/*.json` — judge results, review state, GPU jobs, VLM reviews

**Properties**: Machine-readable, fast to parse, no ambiguity.

### Layer 2: Knowledge Summaries (.ai/)
- `.ai/core/research-context.md` — current research question, hypothesis, constraints
- `.ai/core/methodology.md` — proposed approach, baselines, key design decisions
- `.ai/core/literature.md` — top papers, themes, baselines, gap statement
- `.ai/evolution/decisions.md` — ADRs (append-only)
- `.ai/evolution/negative-results.md` — every failure (append-only)
- `.ai/evolution/experiment-log.md` — brief experiment index (append-only)

**Properties**: Human-readable, concise (50-150 lines each), curated by Memory Synthesizer.

### Layer 3: Reasoning Chain
- `.ai/context_chain.md` — running "why" thread across stages

**Properties**: Captures rationale, not just facts. Each entry answers: what was done, why, what changed, what's next.

## Memory Synthesizer Protocol

The Memory Synthesizer (`skills/memory_sync.md`) is the ONLY skill allowed to update `.ai/` files. It runs after every stage execution.

### Why Separate Memory from Execution?

1. **Quality control**: Executing skills focus on their task; memory quality would suffer as an afterthought.
2. **Consistency**: One skill owns the memory format, preventing drift.
3. **Validation**: State Guardian checks memory quality after synthesis.
4. **Deduplication**: Synthesizer merges overlapping knowledge rather than appending blindly.

### Synthesis Rules

1. **Distill, don't dump**: Stage outputs can be thousands of lines. Memory summaries must be 50-150 lines.
2. **Preserve decisions**: Every major decision gets an ADR entry with context and rationale.
3. **Record failures**: Every failed attempt goes to negative-results.md with "why" analysis.
4. **Update context chain**: Each stage gets exactly one context_chain entry.
5. **Prune stale info**: If new results contradict old summaries, update the summary.

## Git as Continuity Backbone

Git commits serve as an audit trail and recovery mechanism:

- **Stage commits**: `S{N}: <summary>` — marks stage completion
- **Knowledge commits**: `docs(.ai): <summary>` — marks memory updates
- **Protocol commits**: `research(protocol): <hypothesis>` — pre-registers experiment design
- **Result commits**: `research(results): <node_id> — <outcome>` — records experiment results
- **Reflection commits**: `research(reflect): <direction> — <reason>` — outer-loop decisions

The commit history is a recoverable timeline of the entire research process.

## Recovery Scenarios

| Scenario | Recovery |
|----------|----------|
| Pipeline crash mid-stage | `./run.sh resume` — reads registry.yaml, resumes from last stage |
| Corrupted .ai/ file | State Guardian detects, Memory Synthesizer regenerates from outputs |
| Lost experiment results | experiment_tree.json has node metadata; re-run from checkpoint |
| Context chain gap | Memory Synthesizer fills gaps from stage output logs |
| Wrong decision persisted | Append new ADR reversing the old one; update affected summaries |
