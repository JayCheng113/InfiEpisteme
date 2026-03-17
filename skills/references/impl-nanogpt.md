# nanoGPT Implementation Patterns
> Reference for S3/S4. Load when building custom transformer architectures from scratch (<1B params).
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- Custom architecture research (novel attention, residual variants, positional encodings)
- Small models (<1B parameters) where you need full control
- Educational/hackable code (~600 lines total)
- Single-GPU training experiments

## Setup

```bash
git clone https://github.com/karpathy/nanoGPT.git
cd nanoGPT
pip install torch numpy transformers datasets tiktoken wandb tqdm
```

Key files:
- `model.py` — Full GPT model (~300 lines)
- `train.py` — Training loop (~300 lines)
- `config/` — Training configs (override any param via CLI)
- `data/` — Dataset preparation scripts

## Architecture Overview

```python
# model.py core structure
class CausalSelfAttention(nn.Module):    # Multi-head causal attention
class MLP(nn.Module):                     # FFN with GELU
class Block(nn.Module):                   # Attention + MLP + LayerNorm
class GPT(nn.Module):                     # Full model: Embedding + N Blocks + LM Head
```

## Config for Small Models

```python
# Shakespeare character-level (~10M params, trains in minutes)
# config/train_shakespeare_char.py
n_layer = 6
n_head = 6
n_embd = 384
block_size = 256
batch_size = 64
max_iters = 5000
learning_rate = 1e-3
dropout = 0.2

# Custom research model (~125M params)
n_layer = 12
n_head = 12
n_embd = 768
block_size = 1024
batch_size = 12
max_iters = 100000
learning_rate = 6e-4
dropout = 0.0  # 0 for pretraining, >0 for finetuning
```

## Training

```bash
# Prepare data
python data/shakespeare_char/prepare.py

# Single GPU training
python train.py config/train_shakespeare_char.py

# Override any config via CLI
python train.py config/train_shakespeare_char.py \
    --n_layer=8 --n_head=8 --n_embd=512 \
    --max_iters=10000 --wandb_log=True

# Mixed precision + compile (PyTorch 2.0)
python train.py --dtype=bfloat16 --compile=True
```

## Training Loop Essentials

```python
# Key training patterns in train.py
scaler = torch.cuda.amp.GradScaler(enabled=(dtype == 'float16'))
ctx = torch.amp.autocast(device_type=device_type, dtype=ptdtype)

# Gradient accumulation
for micro_step in range(gradient_accumulation_steps):
    with ctx:
        logits, loss = model(X, Y)
        loss = loss / gradient_accumulation_steps
    scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
optimizer.zero_grad(set_to_none=True)

# Learning rate schedule: cosine decay with warmup
lr = min_lr + 0.5 * (learning_rate - min_lr) * (1 + math.cos(math.pi * it / max_iters))
```

## How to Modify for Research

### Custom Attention Mechanism

```python
# In model.py, modify CausalSelfAttention
class CausalSelfAttention(nn.Module):
    def __init__(self, config):
        super().__init__()
        # ADD: your custom projection
        self.custom_proj = nn.Linear(config.n_embd, config.n_embd)
        # Standard Q/K/V
        self.c_attn = nn.Linear(config.n_embd, 3 * config.n_embd, bias=config.bias)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd, bias=config.bias)

    def forward(self, x):
        B, T, C = x.size()
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)
        # ADD: your custom attention logic here
        # e.g., linear attention, sliding window, etc.
        y = torch.nn.functional.scaled_dot_product_attention(
            q, k, v, attn_mask=None, dropout_p=self.dropout, is_causal=True
        )
        return self.c_proj(y)
```

### Adding Custom Residual Connections

```python
# In Block.forward(), modify the residual pattern
def forward(self, x):
    # Standard: x = x + self.attn(self.ln_1(x))
    # Research variant: weighted residual
    attn_out = self.attn(self.ln_1(x))
    x = x + self.alpha * attn_out  # learnable alpha
    mlp_out = self.mlp(self.ln_2(x))
    x = x + self.beta * mlp_out
    return x
```

### Adding New Config Parameters

```python
# In GPTConfig dataclass, add your param
@dataclass
class GPTConfig:
    block_size: int = 1024
    n_layer: int = 12
    n_head: int = 12
    n_embd: int = 768
    my_custom_param: float = 0.1  # ADD: your research param
```

## Performance Tips

```bash
# PyTorch 2.0 compile: ~2x speedup
python train.py --compile=True

# bfloat16 on Ampere+ GPUs (no loss scaling needed)
python train.py --dtype=bfloat16

# float16 on older GPUs (uses GradScaler)
python train.py --dtype=float16

# Typical throughput (A100 40GB):
# 124M model: ~480k tokens/sec with compile+bf16
# 350M model: ~180k tokens/sec with compile+bf16
```

## Data Preparation Pattern

```python
# data/my_dataset/prepare.py
import numpy as np
from datasets import load_dataset
import tiktoken

enc = tiktoken.get_encoding("gpt2")
dataset = load_dataset("my_dataset")

# Tokenize
def process(example):
    ids = enc.encode_ordinary(example['text'])
    ids.append(enc.eot_token)
    return {'ids': ids, 'len': len(ids)}

tokenized = dataset.map(process, remove_columns=['text'])

# Write to binary files
for split, dset in tokenized.items():
    arr = np.memmap(f'{split}.bin', dtype=np.uint16, mode='w+', shape=(total_len,))
    # ... fill array with token ids
```
