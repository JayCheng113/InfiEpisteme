#!/usr/bin/env python3
"""Poll GPU job status until completion.

Usage:
    python3 scripts/gpu_poll.py --node NODE_ID [--timeout SECONDS]
    python3 scripts/gpu_poll.py --all [--timeout SECONDS]

Exits 0 on success, 1 on failure/timeout.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_gpu_jobs():
    path = ROOT / "state" / "GPU_JOBS.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"jobs": {}}

def save_gpu_jobs(jobs):
    path = ROOT / "state" / "GPU_JOBS.json"
    path.write_text(json.dumps(jobs, indent=2))

def check_job(node_id: str, job_info: dict) -> str:
    """Check if a job is still running. Returns: running, complete, failed."""
    mode = job_info.get("mode", "local")
    job_id = job_info["job_id"]

    if mode == "slurm":
        result = subprocess.run(["squeue", "-j", job_id, "-h"], capture_output=True, text=True)
        if result.stdout.strip():
            return "running"
        # Check if output file indicates success
        results_dir = Path(job_info["results_dir"])
        if (results_dir / "metrics.json").exists():
            return "complete"
        return "failed"
    else:
        # Local: check if PID is alive
        try:
            os.kill(int(job_id), 0)
            return "running"
        except ProcessLookupError:
            # Process finished — check results
            results_dir = Path(job_info["results_dir"])
            if (results_dir / "metrics.json").exists():
                return "complete"
            return "failed"

def main():
    parser = argparse.ArgumentParser(description="Poll GPU job status")
    parser.add_argument("--node", help="Node ID to poll")
    parser.add_argument("--all", action="store_true", help="Poll all running jobs")
    parser.add_argument("--timeout", type=int, default=7200, help="Timeout in seconds")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
    args = parser.parse_args()

    start = time.time()
    jobs = load_gpu_jobs()

    nodes_to_poll = []
    if args.all:
        nodes_to_poll = [nid for nid, info in jobs["jobs"].items() if info["status"] == "running"]
    elif args.node:
        nodes_to_poll = [args.node]
    else:
        print("Specify --node or --all", file=sys.stderr)
        sys.exit(1)

    while nodes_to_poll and (time.time() - start) < args.timeout:
        for node_id in list(nodes_to_poll):
            if node_id not in jobs["jobs"]:
                nodes_to_poll.remove(node_id)
                continue
            status = check_job(node_id, jobs["jobs"][node_id])
            jobs["jobs"][node_id]["status"] = status
            if status != "running":
                print(f"Node {node_id}: {status}")
                nodes_to_poll.remove(node_id)

        save_gpu_jobs(jobs)
        if nodes_to_poll:
            time.sleep(args.interval)

    if nodes_to_poll:
        print(f"TIMEOUT: {nodes_to_poll} still running after {args.timeout}s", file=sys.stderr)
        sys.exit(1)

    # Check if any failed
    failed = [nid for nid in (args.node and [args.node] or list(jobs["jobs"].keys()))
              if jobs["jobs"].get(nid, {}).get("status") == "failed"]
    if failed:
        print(f"FAILED nodes: {failed}", file=sys.stderr)
        sys.exit(1)

    print("All jobs complete.")

if __name__ == "__main__":
    main()
