#!/usr/bin/env python3
"""Submit a GPU experiment job.

Usage:
    python3 scripts/gpu_submit.py --node NODE_ID --script PATH --config PATH [--gpu-type TYPE]

Reads config.yaml for GPU settings. Supports local (subprocess) and SLURM modes.
Writes job info to state/GPU_JOBS.json.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

def load_config():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def load_gpu_jobs():
    path = ROOT / "state" / "GPU_JOBS.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"jobs": {}}

def save_gpu_jobs(jobs):
    path = ROOT / "state" / "GPU_JOBS.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Submit GPU experiment job")
    parser.add_argument("--node", required=True, help="Experiment node ID")
    parser.add_argument("--script", required=True, help="Path to training script")
    parser.add_argument("--config", required=True, help="Path to config JSON")
    parser.add_argument("--gpu-type", default=None, help="GPU type override")
    parser.add_argument("--mode", default="local", choices=["local", "slurm"], help="Execution mode")
    args = parser.parse_args()

    config = load_config()
    gpu_type = args.gpu_type or config.get("compute", {}).get("gpu_type", "auto")

    # Create results directory
    results_dir = ROOT / "results" / args.node
    results_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "train.log"

    if args.mode == "slurm":
        # SLURM submission
        slurm_cmd = [
            "sbatch", "--job-name", f"infi-{args.node}",
            "--output", str(log_file),
            "--gres", f"gpu:{gpu_type}:1",
            "python3", args.script, "--config", args.config,
            "--output-dir", str(results_dir),
        ]
        result = subprocess.run(slurm_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"SLURM submission failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        job_id = result.stdout.strip().split()[-1]  # "Submitted batch job 12345"
    else:
        # Local subprocess
        proc = subprocess.Popen(
            ["python3", args.script, "--config", args.config, "--output-dir", str(results_dir)],
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
        )
        job_id = str(proc.pid)

    # Record job
    jobs = load_gpu_jobs()
    jobs["jobs"][args.node] = {
        "job_id": job_id,
        "mode": args.mode,
        "submitted_at": datetime.now().isoformat(),
        "status": "running",
        "gpu_type": gpu_type,
        "script": args.script,
        "config": args.config,
        "log_file": str(log_file),
        "results_dir": str(results_dir),
    }
    save_gpu_jobs(jobs)

    print(f"Submitted job {job_id} for node {args.node} ({args.mode} mode)")

if __name__ == "__main__":
    main()
