#!/usr/bin/env python3
"""Update pipeline state in registry.yaml.

Usage:
    python3 scripts/update_state.py set_running S1        → mark S1 as running
    python3 scripts/update_state.py advance S1             → mark S1 complete, set next running
    python3 scripts/update_state.py fail S1                → mark S1 as failed
    python3 scripts/update_state.py reset S1               → reset S1 and all subsequent to pending
    python3 scripts/update_state.py reset_all              → reset everything to initial state
    python3 scripts/update_state.py set S1 key value       → set a field on S1
"""
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.yaml"
STAGE_ORDER = ["P0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]

def load():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)

def save(reg):
    with open(REGISTRY_PATH, "w") as f:
        yaml.dump(reg, f, default_flow_style=False, sort_keys=False)

def main():
    reg = load()
    cmd = sys.argv[1]

    # Validate stage argument for commands that require one
    if cmd in ("set_running", "advance", "fail", "reset", "set"):
        stage = sys.argv[2]
        if stage not in STAGE_ORDER:
            print(f"ERROR: invalid stage {stage}", file=sys.stderr)
            sys.exit(1)

    if cmd == "set_running":
        stage = sys.argv[2]
        reg["stages"][stage]["status"] = "running"
        reg["current_stage"] = stage
        reg["stages"][stage].setdefault("attempts", 0)
        reg["stages"][stage]["attempts"] += 1
        if stage.startswith("S"):
            reg["phase"] = "research"

    elif cmd == "advance":
        stage = sys.argv[2]
        reg["stages"][stage]["status"] = "complete"
        idx = STAGE_ORDER.index(stage)
        if idx + 1 < len(STAGE_ORDER):
            next_s = STAGE_ORDER[idx + 1]
            reg["current_stage"] = next_s
        else:
            reg["current_stage"] = "COMPLETE"
            reg["phase"] = "complete"

    elif cmd == "fail":
        stage = sys.argv[2]
        reg["stages"][stage]["status"] = "failed"

    elif cmd == "reset":
        stage = sys.argv[2]
        idx = STAGE_ORDER.index(stage)
        for s in STAGE_ORDER[idx:]:
            reg["stages"][s]["status"] = "pending"
            reg["stages"][s].pop("attempts", None)
            reg["stages"][s].pop("last_failure_reason", None)
        reg["current_stage"] = stage
        reg["phase"] = "alignment" if stage == "P0" else "research"

    elif cmd == "reset_all":
        for s in STAGE_ORDER:
            reg["stages"][s]["status"] = "pending"
            for k in ["attempts", "last_failure_reason", "consecutive_same_failure"]:
                reg["stages"][s].pop(k, None)
        reg["current_stage"] = "P0"
        reg["phase"] = "alignment"

    elif cmd == "set":
        stage, key, value = sys.argv[2], sys.argv[3], sys.argv[4]
        # Try to parse as int/float
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        reg["stages"][stage][key] = value

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

    save(reg)

if __name__ == "__main__":
    main()
