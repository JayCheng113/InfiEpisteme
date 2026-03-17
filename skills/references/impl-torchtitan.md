# TorchTitan Implementation Patterns
> Reference for S3/S4. Load when pretraining at scale (8+ GPUs) with composable parallelism.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- Large-scale pretraining (8+ GPUs, multi-node)
- Need composable 4D parallelism (FSDP2 + TP + PP + CP)
- Want PyTorch-native solution (no framework lock-in)
- H100 clusters with Float8 support
- Research on parallelism strategies themselves

## When NOT to Use

- Single GPU experiments (use nanoGPT or LitGPT)
- Finetuning (use TRL or LitGPT)
- < 8 GPUs (use FSDP2 directly)

## Setup

```bash
git clone https://github.com/pytorch/torchtitan.git
cd torchtitan
pip install -e .
# or
pip install torchtitan
```

## 4D Parallelism Overview

```
┌─────────────────────────────────────────┐
│           4D Parallelism                 │
│                                          │
│  FSDP2 — shard params across data ranks  │
│  TP    — split layers across tensor ranks│
│  PP    — split model stages across ranks │
│  CP    — split context across ranks      │
│                                          │
│  Total GPUs = DP × TP × PP × CP         │
└─────────────────────────────────────────┘
```

| Strategy | What it Shards | When to Use |
|----------|---------------|-------------|
| FSDP2 | Parameters + gradients + optimizer | Always (baseline) |
| TP | Individual layers (attention, FFN) | Model too large for single GPU even with FSDP |
| PP | Model stages (groups of layers) | Multi-node, reduce communication |
| CP | Long context sequences | Context > 8K tokens |

## TOML Config Format

```toml
# train_configs/my_experiment.toml

[job]
dump_folder = "./outputs/my_experiment"

[model]
name = "llama3"
flavor = "8B"
tokenizer_path = "./tokenizer.model"

[optimizer]
name = "AdamW"
lr = 3e-4
weight_decay = 0.1

[training]
batch_size = 2
seq_len = 4096
max_norm = 1.0
steps = 10000
warmup_steps = 200
compile = true
dataset = "c4"

[parallelism]
dp_shard = 4     # FSDP sharding degree
dp_replicate = 1 # data replication
tp_degree = 2    # tensor parallel
pp_degree = 1    # pipeline parallel
cp_degree = 1    # context parallel

[checkpoint]
interval = 1000
folder = "checkpoints"

[metrics]
enable_tensorboard = true
log_freq = 10

[float8]
enable_float8_linear = false  # H100 only
```

## Running Training

```bash
# Single node, 8 GPUs
torchrun --nproc_per_node=8 train.py --job.config_file train_configs/my_experiment.toml

# Multi-node (2 nodes, 8 GPUs each)
torchrun --nnodes=2 --nproc_per_node=8 \
    --rdzv_backend=c10d --rdzv_endpoint=master:29500 \
    train.py --job.config_file train_configs/my_experiment.toml

# Override config via CLI
torchrun --nproc_per_node=8 train.py \
    --job.config_file train_configs/llama3_8b.toml \
    --training.steps 5000 \
    --parallelism.tp_degree 4
```

## Parallelism Configurations by Scale

```toml
# 8 GPUs, 8B model — FSDP only
[parallelism]
dp_shard = 8
tp_degree = 1
pp_degree = 1

# 8 GPUs, 70B model — FSDP + TP
[parallelism]
dp_shard = 4
tp_degree = 2
pp_degree = 1

# 32 GPUs, 70B model — FSDP + TP + PP
[parallelism]
dp_shard = 4
tp_degree = 2
pp_degree = 4

# 64 GPUs, 405B model — Full 4D
[parallelism]
dp_shard = 4
tp_degree = 4
pp_degree = 4
cp_degree = 1
```

## Float8 on H100s

```toml
# Enable Float8 for ~1.5x throughput on H100
[float8]
enable_float8_linear = true
enable_fsdp_float8_all_gather = true
precompute_float8_dynamic_scale_for_fsdp = true

# Requires: H100 GPU + PyTorch 2.4+
# Speedup: ~30-50% over bf16
# Accuracy: minimal degradation for pretraining
```

## Supported Models

| Model | Sizes | Config File |
|-------|-------|-------------|
| LLaMA 3 | 8B, 70B, 405B | `llama3_8b.toml`, `llama3_70b.toml` |
| LLaMA 3.1 | 8B, 70B, 405B | `llama3_1_*.toml` |
| Mixtral | 8x7B | `mixtral_8x7b.toml` |

## Key Source Files

```
torchtitan/
├── models/
│   └── llama/          # Model definitions
├── parallelisms/
│   ├── parallelize_llama.py  # How parallelism is applied
│   └── pipeline_llama.py     # Pipeline parallel stages
├── train.py            # Main training loop
└── config_manager.py   # TOML config parsing
```

## Adding a Custom Model

```python
# 1. Define model in torchtitan/models/my_model/
# 2. Register in torchtitan/models/__init__.py
# 3. Create parallelize function
# 4. Add TOML config

# The parallelize function applies parallelism strategies:
def parallelize_my_model(model, world_mesh, parallel_dims, job_config):
    # Apply TP to attention and FFN
    for layer in model.layers:
        parallelize_module(layer.attn, mesh["tp"], {...})
        parallelize_module(layer.ffn, mesh["tp"], {...})
    # Apply FSDP
    for layer in model.layers:
        fully_shard(layer, mesh=mesh["dp"])
    fully_shard(model, mesh=mesh["dp"])
    return model
```

## When to Prefer Over Alternatives

| Scenario | Best Tool |
|----------|-----------|
| Single GPU, custom arch | nanoGPT |
| 1-4 GPUs, finetuning | LitGPT / TRL |
| 1-8 GPUs, full finetune | FSDP2 directly |
| 8+ GPUs, pretraining | **TorchTitan** |
| Need Float8 + 4D parallel | **TorchTitan** |
| Quick LoRA finetune | LitGPT / Unsloth |
