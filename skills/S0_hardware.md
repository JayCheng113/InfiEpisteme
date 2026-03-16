# S0 Hardware — Hardware Detection and Profiling

> Pre-stage. Runs once at pipeline start to detect hardware capabilities.
> Inherits: `_common.md`

## Before You Start

1. Check if `hardware_profile.json` already exists and is recent (< 24 hours old).
   - If recent and valid: skip detection entirely.
   - If stale or missing: proceed with detection.
2. Read `config.yaml` — check compute settings for context.

## Your Role

You detect the current machine's hardware capabilities and write a structured profile that all downstream skills use to adapt their experiment plans, batch sizes, and parallelism strategies.

## Process

### Step 1: Detect Hardware via MCP (preferred) or Fallback

**GPU Detection** (try in order):

1. **System Monitor MCP** (preferred):
   - Use `mcp__system-monitor__get_gpu_info` to get GPU details.
   - Use `mcp__system-monitor__get_cpu_info` for CPU info.
   - Use `mcp__system-monitor__get_memory_info` for RAM.
   - Use `mcp__system-monitor__get_disk_info` for storage.

2. **Fallback** (if MCP unavailable):
   ```bash
   # GPU
   nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader 2>/dev/null
   # Or via PyTorch
   python3 -c "import torch; [print(f'{i}: {torch.cuda.get_device_name(i)}, {torch.cuda.get_device_properties(i).total_mem // 1024**2}MB') for i in range(torch.cuda.device_count())]" 2>/dev/null
   # CPU
   sysctl -n machdep.cpu.brand_string 2>/dev/null || lscpu 2>/dev/null
   # Memory
   python3 -c "import psutil; m=psutil.virtual_memory(); print(f'total={m.total/1024**3:.0f}GB available={m.available/1024**3:.0f}GB')" 2>/dev/null
   # Disk
   df -h . 2>/dev/null
   ```

3. **No GPU detected**: Record `gpu.count: 0` and set recommendations for CPU-only or SSH remote execution.

### Step 2: Detect CUDA Version

```bash
nvcc --version 2>/dev/null || nvidia-smi 2>/dev/null | grep "CUDA Version"
```

### Step 3: Generate Recommendations

Based on detected hardware, compute:

- **max_batch_size_estimate**: Based on VRAM per GPU
  - 80GB VRAM: ~32 for 7B model, ~8 for 70B model
  - 24GB VRAM: ~8 for 7B model, quantization needed for larger
  - 16GB VRAM: ~4 for 7B model, consider LoRA/QLoRA
  - No GPU: CPU-only, very small models or remote execution

- **distributed_training**: Whether DDP/FSDP is available
  - 2+ GPUs: recommend DDP or FSDP
  - 1 GPU: single-device, gradient accumulation if needed
  - 0 GPUs: flag for SSH remote execution

- **parallel_experiments**: How many experiments can run simultaneously
  - Based on GPU count and VRAM

- **estimated_gpu_hours_available**: From `config.yaml` compute budget

### Step 4: Write `hardware_profile.json`

```json
{
  "timestamp": "ISO-8601",
  "detection_method": "system_monitor_mcp" | "nvidia_smi" | "pytorch" | "cpu_only",
  "gpu": {
    "count": N,
    "devices": [
      {
        "id": 0,
        "name": "GPU Name",
        "vram_mb": N,
        "compute_capability": "X.Y"
      }
    ],
    "total_vram_mb": N,
    "driver_version": "X.Y.Z",
    "cuda_version": "X.Y"
  },
  "cpu": {
    "model": "CPU Name",
    "cores": N,
    "threads": N
  },
  "memory": {
    "total_gb": N,
    "available_gb": N
  },
  "disk": {
    "total_gb": N,
    "available_gb": N
  },
  "recommendations": {
    "max_batch_size_estimate": "description based on VRAM",
    "distributed_training": "description of available parallelism",
    "parallel_experiments": N,
    "estimated_gpu_hours_available": "from config.yaml budget",
    "constraints": ["list of notable constraints, e.g. 'VRAM < 16GB: avoid large model training'"],
    "execution_mode": "local_gpu" | "local_cpu" | "ssh_remote"
  }
}
```

### Step 5: Validate Profile

1. Verify JSON is well-formed.
2. Verify GPU count matches device list length.
3. Verify total_vram_mb = sum of device VRAM values.
4. If no GPU and `config.yaml` specifies GPU experiments: warn about mismatch.

## Output

| File | Action |
|------|--------|
| `hardware_profile.json` | Create hardware profile |

## Rules

- Report actual hardware honestly — do not inflate or guess.
- If detection fails for a component, set its values to `null` and note in `detection_method`.
- The profile must be valid JSON parseable by downstream skills.
- Do not install any packages — only use what's already available.
- This skill is read-only for all other files (only writes `hardware_profile.json`).

## When Done

- `hardware_profile.json` exists with complete hardware profile.
- Log a brief summary: "Hardware detected: {gpu_count}x {gpu_name}, {ram}GB RAM, {mode}."
- No commit needed — this is a runtime artifact.
