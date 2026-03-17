# FSDP2 Implementation Patterns
> Reference for S3/S4. Load when model exceeds single GPU memory and you need distributed training.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- Model parameters don't fit on a single GPU
- 2-8 GPU training (for 8+ GPUs, consider TorchTitan)
- Need fine-grained control over sharding (vs. framework abstractions)
- Full finetuning (not LoRA) of large models

## 5 Critical Rules

1. **Always use `torchrun`** — never `python` directly
2. **Shard bottom-up** — `fully_shard` inner modules first, then outer
3. **Use `model(input)` not `model.forward(input)`** — hooks won't fire otherwise
4. **Create optimizer AFTER sharding** — optimizer must see sharded params
5. **Use DCP for checkpointing** — `torch.save` won't work with sharded state

## Minimal Implementation

```python
# train_fsdp.py
import torch
import torch.distributed as dist
from torch.distributed._composable.fsdp import fully_shard, MixedPrecisionPolicy

def main():
    dist.init_process_group("nccl")
    rank = dist.get_device_mesh("cuda").get_local_rank()
    torch.cuda.set_device(rank)

    # 1. Build model on meta device (no memory until materialized)
    model = MyModel()
    model.to("cuda")

    # 2. Mixed precision policy
    mp_policy = MixedPrecisionPolicy(
        param_dtype=torch.bfloat16,
        reduce_dtype=torch.float32,
    )

    # 3. Shard bottom-up: inner modules first
    for layer in model.layers:
        fully_shard(layer, mp_policy=mp_policy)
    fully_shard(model, mp_policy=mp_policy)  # root last

    # 4. Optimizer AFTER sharding
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # 5. Training loop
    for batch in dataloader:
        optimizer.zero_grad()
        loss = model(batch)  # NOT model.forward(batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

    dist.destroy_process_group()

if __name__ == "__main__":
    main()
```

```bash
# Launch with torchrun
torchrun --nproc_per_node=4 train_fsdp.py
```

## Mixed Precision Config

```python
from torch.distributed._composable.fsdp import MixedPrecisionPolicy

# bf16 compute, fp32 reduction (recommended for training stability)
mp_policy = MixedPrecisionPolicy(
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.float32,
)

# Full bf16 (faster, slightly less stable)
mp_policy = MixedPrecisionPolicy(
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.bfloat16,
)

# fp32 only (debugging)
mp_policy = MixedPrecisionPolicy()
```

## Gradient Accumulation

```python
# FSDP2 requires explicit sync control for gradient accumulation
gradient_accumulation_steps = 4

for step, batch in enumerate(dataloader):
    # Disable gradient sync for accumulation steps
    is_accumulating = (step + 1) % gradient_accumulation_steps != 0

    with model.set_requires_gradient_sync(not is_accumulating):
        loss = model(batch) / gradient_accumulation_steps
        loss.backward()

    if not is_accumulating:
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad()
```

## Memory Tuning: reshard_after_forward

```python
from torch.distributed._composable.fsdp import fully_shard

# Default: reshard params after forward (saves memory, costs communication)
fully_shard(layer, reshard_after_forward=True)

# Keep params after forward (uses more memory, faster backward)
# Use for small models or when you have memory headroom
fully_shard(layer, reshard_after_forward=False)

# Selective: keep root, reshard inner layers
for layer in model.layers:
    fully_shard(layer, reshard_after_forward=True)
fully_shard(model, reshard_after_forward=False)  # root keeps params
```

## DCP Checkpointing

```python
import torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint.state_dict import (
    get_state_dict, set_state_dict, StateDictOptions
)

# Save checkpoint
def save_checkpoint(model, optimizer, step, path):
    model_state, optimizer_state = get_state_dict(model, optimizer)
    state = {
        "model": model_state,
        "optimizer": optimizer_state,
        "step": step,
    }
    dcp.save(state, checkpoint_id=path)

# Load checkpoint
def load_checkpoint(model, optimizer, path):
    model_state, optimizer_state = get_state_dict(model, optimizer)
    state = {
        "model": model_state,
        "optimizer": optimizer_state,
    }
    dcp.load(state, checkpoint_id=path)
    set_state_dict(
        model, optimizer,
        model_state_dict=state["model"],
        optim_state_dict=state["optimizer"],
    )
```

## Applying to a Transformer Model

```python
from torch.distributed._composable.fsdp import fully_shard, MixedPrecisionPolicy

def shard_transformer(model, mp_policy):
    """Apply FSDP2 to a standard transformer model."""
    # Shard embedding (if large vocabulary)
    fully_shard(model.embed, mp_policy=mp_policy)

    # Shard each transformer block
    for block in model.blocks:
        # Optionally shard sub-modules for very large models
        # fully_shard(block.attn, mp_policy=mp_policy)
        # fully_shard(block.ffn, mp_policy=mp_policy)
        fully_shard(block, mp_policy=mp_policy)

    # Shard output head
    fully_shard(model.head, mp_policy=mp_policy)

    # Root shard last
    fully_shard(model, mp_policy=mp_policy)

    return model
```

## Learning Rate Scaling

```python
# Scale LR with number of GPUs (linear scaling rule)
base_lr = 1e-4
world_size = dist.get_world_size()
scaled_lr = base_lr * world_size  # or sqrt(world_size) for conservative

# Use warmup to stabilize
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_steps)
warmup = torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.1, total_iters=warmup_steps)
scheduler = torch.optim.lr_scheduler.SequentialLR(optimizer, [warmup, scheduler], milestones=[warmup_steps])
```

## Debug Checklist

1. **NCCL timeout** → Set `NCCL_DEBUG=INFO`, check all GPUs are visible
2. **OOM on one rank** → Uneven model sharding; ensure all layers are sharded
3. **Loss NaN** → Check mixed precision config; try fp32 reduce
4. **Slow training** → Check `reshard_after_forward`; ensure gradient sync is disabled during accumulation
5. **Checkpoint won't load** → Must use DCP, not `torch.save`; ensure same world size
6. **Hanging** → One rank crashed silently; check per-rank logs

```bash
# Useful environment variables
export NCCL_DEBUG=INFO           # Debug NCCL communication
export CUDA_VISIBLE_DEVICES=0,1,2,3  # Select GPUs
export TORCH_DISTRIBUTED_DEBUG=DETAIL  # Detailed distributed debug

# Launch with error handling
torchrun --nproc_per_node=4 --rdzv_backend=c10d \
    --rdzv_endpoint=localhost:29500 train_fsdp.py
```

## FSDP2 vs FSDP1 (Legacy)

| Feature | FSDP1 | FSDP2 |
|---------|-------|-------|
| API | `FullyShardedDataParallel` wrapper | `fully_shard()` composable |
| Composability | Limited | Works with TP, CP, compile |
| Gradient accumulation | `no_sync()` context | `set_requires_gradient_sync()` |
| Checkpointing | Custom | DCP native |
| Status | Maintenance mode | Active development |

Always use FSDP2 for new projects.
