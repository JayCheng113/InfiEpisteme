#!/usr/bin/env python3
"""State Guardian — validates and repairs pipeline state after each skill execution.

Deterministic Python logic (not LLM). Ensures state integrity even when
Claude Code misses updates.

Usage:
    python3 scripts/state_guard.py verify --stage S1    → verify S1 outputs and state
    python3 scripts/state_guard.py advance --stage S1   → read JUDGE_RESULT.json, advance if passed
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STAGE_ORDER = ["P0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


def load_registry():
    with open(ROOT / "registry.yaml") as f:
        return yaml.safe_load(f)

def save_registry(reg):
    with open(ROOT / "registry.yaml", "w") as f:
        yaml.dump(reg, f, default_flow_style=False, sort_keys=False)

def load_pipeline():
    """Parse PIPELINE.md for stage definitions (expected_outputs, registry_fields)."""
    pipeline_path = ROOT / "PIPELINE.md"
    if not pipeline_path.exists():
        return {}
    content = pipeline_path.read_text()
    # Simple YAML block extraction from markdown fenced blocks
    stages = {}
    current_stage = None
    in_yaml = False
    yaml_lines = []

    for line in content.split("\n"):
        if re.match(r'^###\s+(P0|S\d)', line):
            if current_stage and yaml_lines:
                try:
                    stages[current_stage] = yaml.safe_load("\n".join(yaml_lines))
                except yaml.YAMLError:
                    pass
            current_stage = re.match(r'^###\s+(P0|S\d)', line).group(1)
            yaml_lines = []
            in_yaml = False
        elif line.strip() == "```yaml":
            in_yaml = True
        elif line.strip() == "```" and in_yaml:
            in_yaml = False
        elif in_yaml:
            yaml_lines.append(line)

    if current_stage and yaml_lines:
        try:
            stages[current_stage] = yaml.safe_load("\n".join(yaml_lines))
        except yaml.YAMLError:
            pass

    return stages


def verify_stage(stage: str) -> dict:
    """Verify a stage's outputs and state, attempt repairs."""
    report = {
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "repairs": [],
        "warnings": [],
        "passed": True,
    }

    reg = load_registry()
    pipeline = load_pipeline()
    stage_def = pipeline.get(stage, {})

    # Check 1: Expected output files exist
    expected_outputs = stage_def.get("expected_outputs", [])
    for output_file in expected_outputs:
        path = ROOT / output_file
        if path.exists():
            report["checks"].append({"file": output_file, "exists": True})
        else:
            report["checks"].append({"file": output_file, "exists": False})
            report["passed"] = False

    # Check 2: .ai/ docs updated (modification time + content quality)
    expected_ai = stage_def.get("expected_ai_updates", [])
    for ai_file in expected_ai:
        path = ROOT / ai_file
        if path.exists():
            mtime = os.path.getmtime(path)
            age_hours = (datetime.now().timestamp() - mtime) / 3600
            if age_hours > 24:
                report["warnings"].append(f"{ai_file} not updated recently ({age_hours:.0f}h old)")
            # Content quality check
            content = path.read_text()
            quality = _check_ai_content_quality(ai_file, content)
            if quality:
                report["warnings"].append(f"{ai_file}: {quality}")
        else:
            report["warnings"].append(f"{ai_file} does not exist")

    # Check 2.5: Memory sync result
    mem_sync_path = ROOT / "state" / "MEMORY_SYNC_RESULT.json"
    if mem_sync_path.exists():
        mem_result = json.loads(mem_sync_path.read_text())
        if mem_result.get("stage") == stage:
            report["checks"].append({"file": "memory_sync", "exists": True})
        else:
            report["warnings"].append("MEMORY_SYNC_RESULT.json exists but for different stage")

    # Check 2.6: Context chain has entry for this stage
    chain_path = ROOT / ".ai" / "context_chain.md"
    if chain_path.exists():
        chain_content = chain_path.read_text()
        if f"## {stage}:" in chain_content:
            report["checks"].append({"file": "context_chain_entry", "exists": True})
        else:
            report["warnings"].append(f"context_chain.md missing entry for {stage}")

    # Check 3: Registry fields
    registry_fields = stage_def.get("registry_fields", {})
    stage_info = reg["stages"].get(stage, {})
    for field, constraint in registry_fields.items():
        actual = stage_info.get(field)
        if actual is None:
            # Attempt repair: infer from output files
            repaired_value = _infer_field(stage, field)
            if repaired_value is not None:
                reg["stages"][stage][field] = repaired_value
                report["repairs"].append(f"Set {stage}.{field} = {repaired_value} (inferred)")
            else:
                report["warnings"].append(f"{stage}.{field} missing, could not infer")

    # Check 4: experiment_tree.json consistency (for S3, S4)
    if stage in ("S3", "S4"):
        tree_path = ROOT / "experiment_tree.json"
        if tree_path.exists():
            tree = json.loads(tree_path.read_text())
            nodes = tree.get("nodes", [])
            for node in nodes:
                if node.get("status") == "complete" and node.get("results_path"):
                    results_path = ROOT / node["results_path"]
                    if not results_path.exists():
                        report["warnings"].append(
                            f"Node {node['id']} claims complete but {node['results_path']} missing"
                        )

    # Save repairs if any
    if report["repairs"]:
        save_registry(reg)

    # Write guard result
    guard_path = ROOT / "state" / "GUARD_RESULT.json"
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    guard_path.write_text(json.dumps(report, indent=2))

    return report


def advance_stage(stage: str) -> bool:
    """Read JUDGE_RESULT.json and advance pipeline if passed."""
    judge_path = ROOT / "state" / "JUDGE_RESULT.json"

    if not judge_path.exists():
        print(f"ERROR: state/JUDGE_RESULT.json not found", file=sys.stderr)
        return False

    result = json.loads(judge_path.read_text())

    # Handle both direct JSON and claude -p wrapped output
    if "result" in result and isinstance(result["result"], str):
        # Try to extract JSON from the result string
        text = result["result"]
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            try:
                result = json.loads(text[json_start:json_end])
            except json.JSONDecodeError:
                pass

    passed = result.get("passed", False)
    if isinstance(passed, str):
        passed = passed.lower() in ("true", "yes", "1")

    reg = load_registry()

    if passed:
        reg["stages"][stage]["status"] = "complete"
        idx = STAGE_ORDER.index(stage)
        if idx + 1 < len(STAGE_ORDER):
            next_s = STAGE_ORDER[idx + 1]
            reg["current_stage"] = next_s
        else:
            reg["current_stage"] = "COMPLETE"
            reg["phase"] = "complete"
        save_registry(reg)
        print(f"PASSED — advanced to {reg['current_stage']}")
        return True
    else:
        reasons = result.get("reasons", result.get("retry_guidance", "unknown"))
        reg["stages"][stage]["last_failure_reason"] = str(reasons)[:500]

        # Circuit breaker: track consecutive same-criterion failures
        prev_reason = reg["stages"][stage].get("prev_failure_reason", "")
        if str(reasons)[:100] == prev_reason[:100]:
            count = reg["stages"][stage].get("consecutive_same_failure", 0) + 1
            reg["stages"][stage]["consecutive_same_failure"] = count
            if count >= 3:
                print(f"CIRCUIT BREAKER: {stage} failed 3x on same criterion. Pausing.", file=sys.stderr)
        else:
            reg["stages"][stage]["consecutive_same_failure"] = 1
        reg["stages"][stage]["prev_failure_reason"] = str(reasons)[:100]

        save_registry(reg)
        print(f"FAILED — {reasons}")
        return False


def _check_ai_content_quality(ai_file: str, content: str) -> str | None:
    """Check if an .ai/ file has meaningful content. Returns warning string or None."""
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("---") and not l.startswith("#") and not l.startswith(">") and not l.startswith("<!--")]

    # Skip template-only files (contain "To be filled")
    if any("to be filled" in l.lower() for l in lines):
        return "still contains template placeholders ('To be filled')"

    # Minimum content thresholds by file type
    if "literature.md" in ai_file:
        if len(lines) < 10:
            return f"too short ({len(lines)} content lines, need ≥10)"
        # Should contain at least some paper references
        citations = re.findall(r'\[[\w\s,]+\d{4}\]', content)
        if len(citations) < 3:
            return f"only {len(citations)} citations found (need ≥3)"

    elif "methodology.md" in ai_file:
        if len(lines) < 5:
            return f"too short ({len(lines)} content lines, need ≥5)"
        # Should explain "why" not just "what"
        if "because" not in content.lower() and "reason" not in content.lower() and "since" not in content.lower():
            return "missing rationale (no 'because'/'reason' found — methodology should explain WHY)"

    elif "research-context.md" in ai_file:
        if len(lines) < 3:
            return f"too short ({len(lines)} content lines, need ≥3)"

    elif "negative-results.md" in ai_file:
        pass  # Append-only, no minimum

    elif "decisions.md" in ai_file:
        pass  # Append-only, no minimum

    elif "experiment-log.md" in ai_file:
        pass  # Append-only, no minimum

    elif "context_chain.md" in ai_file:
        if len(lines) < 3:
            return f"too short ({len(lines)} content lines)"

    return None


def _infer_field(stage: str, field: str):
    """Try to infer a registry field from output files."""
    if stage == "S1" and field == "papers_reviewed":
        rw_path = ROOT / "RELATED_WORK.md"
        if rw_path.exists():
            content = rw_path.read_text()
            citations = re.findall(r'\[[\w\s]+,\s*\d{4}\]', content)
            return len(set(citations))
    if stage == "S1" and field == "baselines_identified":
        bl_path = ROOT / "BASELINES.md"
        if bl_path.exists():
            return bl_path.read_text().count("## Baseline")
    if stage == "S7" and field == "review_cycles":
        reviews_dir = ROOT / "reviews"
        if reviews_dir.exists():
            cycles = [d.name for d in reviews_dir.iterdir() if d.is_dir() and d.name.startswith("cycle_")]
            return len(cycles)
    return None


def main():
    parser = argparse.ArgumentParser(description="State Guardian")
    parser.add_argument("command", choices=["verify", "advance"])
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()

    if args.command == "verify":
        report = verify_stage(args.stage)
        n_checks = len(report["checks"])
        n_passed = sum(1 for c in report["checks"] if c.get("exists", True))
        n_repairs = len(report["repairs"])
        n_warnings = len(report["warnings"])
        print(f"Guard: {n_passed}/{n_checks} checks passed, {n_repairs} repairs, {n_warnings} warnings")
        for r in report["repairs"]:
            print(f"  REPAIR: {r}")
        for w in report["warnings"]:
            print(f"  WARN: {w}")

    elif args.command == "advance":
        passed = advance_stage(args.stage)
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
