#!/usr/bin/env python3
"""Read pipeline state from registry.yaml and output to stdout.

Usage:
    python3 scripts/parse_state.py current_stage     → prints current stage name
    python3 scripts/parse_state.py stage_status S1    → prints status of S1
    python3 scripts/parse_state.py status             → prints full human-readable status
    python3 scripts/parse_state.py next_stage S1      → prints next stage after S1
"""
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE_ORDER = ["P0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]

def load_registry():
    with open(ROOT / "registry.yaml") as f:
        return yaml.safe_load(f)

def main():
    reg = load_registry()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "current_stage":
        print(reg["current_stage"])
    elif cmd == "stage_status":
        stage = sys.argv[2]
        print(reg["stages"][stage].get("status", "unknown"))
    elif cmd == "next_stage":
        stage = sys.argv[2]
        idx = STAGE_ORDER.index(stage)
        print(STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else "COMPLETE")
    elif cmd == "status":
        print(f"Phase: {reg['phase']}")
        print(f"Current Stage: {reg['current_stage']}")
        print()
        for s in STAGE_ORDER:
            info = reg["stages"].get(s, {})
            status = info.get("status", "unknown")
            extra_parts = []
            if s == "S1" and "papers_reviewed" in info:
                extra_parts.append(f"papers: {info['papers_reviewed']}/{info.get('target', 20)}")
            if s == "S4" and "tree_stages_complete" in info:
                extra_parts.append(f"tree: {info['tree_stages_complete']}/{info.get('tree_stages_total', 4)}")
            if s == "S7" and "review_cycles" in info:
                extra_parts.append(f"cycles: {info['review_cycles']}, score: {info.get('current_score', 0):.1f}")
            if "attempts" in info and info["attempts"] > 0:
                extra_parts.append(f"attempts: {info['attempts']}")
            extra = f" ({', '.join(extra_parts)})" if extra_parts else ""
            print(f"  {s}: {status}{extra}")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
