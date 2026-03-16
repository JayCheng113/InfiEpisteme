# Common Preamble — InfiEpisteme Research Pipeline

> This preamble is shared across all skills. Every skill implicitly inherits these rules.

## Project Identity

You are operating inside **InfiEpisteme**, an automated research pipeline that takes a research direction and delivers a peer-review-quality paper, clean code, and organized results. The pipeline runs as a sequence of stages: P0 -> S0 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7 -> S8 -> COMPLETE.

You are a Claude Code skill — a self-contained instruction set that reads inputs, performs work, and writes outputs. You must be **idempotent**: if invoked twice on the same inputs, you produce the same outputs without duplicating work.

## Before You Start — State Loading

1. **Read `registry.yaml`** — determine current stage, attempt count, and any stage-specific counters.
2. **Read `config.yaml`** — get compute budget, target venue, target score, cross-review settings.
3. **Read `experiment_tree.json`** — if your skill touches the experiment tree.
4. **Check `state/JUDGE_RESULT.json`** — if it exists and shows `"passed": false` for your stage:
   - Read the `retry_guidance` field carefully.
   - Read the `criteria` array to see which checks failed.
   - Address those specific failures in this run. Do not start from scratch unless retry_guidance says to.
5. **Check existing outputs** — if the expected output files already exist and are complete, skip that work. Only redo work that failed or is missing.

## .ai/ Knowledge Base Protocol

### Loading (before work)
- Always read `.ai/core/research-context.md` — the current research question and hypothesis.
- Read additional `.ai/` documents per the loading rules in `.ai/_loading-rules.md`.
- Maximum 5 documents loaded per skill invocation.
- Priority order: research-context > methodology > literature > decisions > negative-results.

### Maintenance (after work)
**You do NOT need to update .ai/ files.** A dedicated Memory Synthesizer (`skills/memory_sync.md`) runs automatically after your skill completes and handles all .ai/ updates. Focus on producing your stage outputs.

Exception: If you discover a critical failure during your work, you MAY append to `.ai/evolution/negative-results.md` immediately (don't wait for memory sync).

## MCP Tool Policy

When MCP tools are available, prefer them over Python scripts. If an MCP tool call fails (not installed, connection error, timeout), fall back to the corresponding Python script.

| Task | MCP Tool (preferred) | Fallback |
|------|---------------------|----------|
| Paper search | `mcp__semantic-scholar__search_papers` | `python3 scripts/scholarly_search.py search` |
| Paper details | `mcp__semantic-scholar__get_paper_details` | `python3 scripts/scholarly_search.py bibtex` |
| Hardware info | `mcp__system-monitor__get_gpu_info` etc. | `nvidia-smi` / `python3 -c "import psutil; ..."` |
| Remote execution | `mcp__ssh__execute_command` | `python3 scripts/gpu_submit.py` / `gpu_poll.py` |

## Hardware-Aware Design

If your skill involves **experiment design, code implementation, or resource estimation**, read `hardware_profile.json` before starting. Adapt your plan to hardware capabilities:

- **No GPU** → CPU-only plan or flag for SSH remote execution
- **Single GPU, VRAM < 16GB** → gradient accumulation, mixed precision, small batch, avoid large models; consider quantization (QLoRA)
- **Single GPU, VRAM ≥ 16GB** → standard training; use mixed precision for efficiency
- **Multi-GPU** → use DDP/FSDP; set `parallel_experiments` from hardware profile
- **VRAM < model requirement** → consider model parallelism, offloading, or smaller model variants

If `hardware_profile.json` does not exist, proceed without hardware constraints but note the limitation.

## Anti-Hallucination Rules

These rules are **non-negotiable**:

1. **Every citation must be real.** If you cite [Author, Year], that paper must exist. Verify via Semantic Scholar MCP (`mcp__semantic-scholar__search_papers`) or fallback `python3 scripts/scholarly_search.py`.
2. **Never fabricate paper titles, authors, venues, or years.** If unsure, search first.
3. **Never fabricate experimental numbers.** Every number in a table must come from an actual experiment run or a verified published paper.
4. **Every \cite{} in LaTeX must match an entry in bibliography.bib.** No phantom citations.
5. **If you cannot verify a claim, say so explicitly** rather than inventing a reference.
6. **Citation key format must be consistent**: `author_year_firstword` (e.g., `vaswani_2017_attention`).
7. **Never generate BibTeX from LLM memory.** BibTeX must come from Semantic Scholar MCP, DOI lookup, or an authoritative source.
8. **Every citation must be confirmed in 2+ independent sources** (Semantic Scholar + arXiv or CrossRef).
9. **Full citation verification protocol**: see `skills/references/citation-verification.md`.

## Output Rules

### File Scope
- Only create or modify files that your skill's "Output" section specifies.
- Never modify files owned by another skill unless explicitly instructed.
- Never delete files created by previous stages.

### Commit Format
Stage work commits: `<stage>: <summary>` (e.g., `S1: complete literature survey with 25 papers`)
Knowledge commits: `docs(.ai): <summary>`
Experiment protocol commits: `research(protocol): {hypothesis} — {approach}` (must be committed BEFORE running the experiment)
Experiment result commits: `research(results): {node_id} — {metric}={value}`
Outer-loop reflection commits: `research(reflect): {direction} — {reason}`

### Idempotency
- Before writing an output file, check if it already exists with valid content.
- If it does, skip or update incrementally rather than overwriting from scratch.
- Use timestamps or checksums when possible to detect staleness.

## Error Handling

When something fails:
1. **Log the failure** to `.ai/evolution/negative-results.md` with:
   - What was attempted
   - What went wrong (error message or unexpected result)
   - Why it likely failed (your hypothesis)
   - Implications for future attempts
2. **Do not silently retry** without logging the failure first.
3. **Do not proceed past a blocking failure** — if a critical input is missing or corrupted, stop and report clearly.

## Retry Handling

When invoked as a retry (state/JUDGE_RESULT.json shows failure):
1. Read `retry_guidance` from the judge result.
2. Read `criteria` array to find which checks failed.
3. Focus your work on the failed criteria. Do not redo passing criteria.
4. If the same criterion has failed 3+ times, add a detailed note to `.ai/evolution/negative-results.md` explaining the pattern and stop.

## When Done

Every skill must end by:
1. Writing all expected output files.
2. Reporting a brief summary of what was produced and any concerns.
3. The orchestrator will then invoke `memory_sync.md` to consolidate knowledge into `.ai/`, followed by `judge.md` to evaluate your outputs.
