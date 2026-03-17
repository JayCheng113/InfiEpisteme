# LitGPT Implementation Patterns
> Reference for S3/S4. Load when using existing architectures (LLaMA, Mistral, Qwen, Gemma) or finetuning.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- Leveraging pretrained architectures (20+ supported: LLaMA, Mistral, Qwen, Gemma, Phi, etc.)
- LoRA/QLoRA finetuning on consumer GPUs
- Pretraining with established architectures
- Need HuggingFace checkpoint interop

## Setup

```bash
pip install litgpt[all]
# or from source
git clone https://github.com/Lightning-AI/litgpt.git
cd litgpt && pip install -e '.[all]'
```

## Key Commands

```bash
# Download a model
litgpt download meta-llama/Llama-3.1-8B-Instruct --access_token YOUR_TOKEN

# Finetune with LoRA
litgpt finetune_lora meta-llama/Llama-3.1-8B-Instruct \
    --data JSON --data.json_path my_data.json \
    --train.epochs 3 --train.lr 3e-4

# Pretrain from scratch
litgpt pretrain --config my_config.yaml

# Chat / inference
litgpt chat meta-llama/Llama-3.1-8B-Instruct

# Convert to/from HuggingFace
litgpt convert_to_hf checkpoints/my-model out/hf-model
litgpt convert_from_hf meta-llama/Llama-3.1-8B out/litgpt-model
```

## LoRA/QLoRA Config for Memory-Constrained GPUs

```yaml
# finetune_lora_config.yaml — fits on 24GB GPU for 7B model
model_name: meta-llama/Llama-3.1-8B-Instruct

# LoRA parameters
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_query: true
lora_key: false
lora_value: true
lora_projection: false
lora_mlp: true
lora_head: false

# Training
train:
  epochs: 3
  lr: 3e-4
  batch_size: 4
  micro_batch_size: 1  # gradient accumulation = batch_size / micro_batch_size
  warmup_steps: 100
  max_seq_length: 2048

# QLoRA (4-bit quantization) — fits 7B on 16GB
quantize: bnb.nf4-dq  # options: bnb.nf4, bnb.nf4-dq, bnb.fp4, bnb.fp4-dq
```

```bash
# Run with config
litgpt finetune_lora --config finetune_lora_config.yaml
```

## Data Format

```json
// my_data.json — instruction format
[
  {
    "instruction": "Summarize the following text.",
    "input": "Long text here...",
    "output": "Summary here..."
  }
]

// Alternative: simple text format for pretraining
// One document per line in .txt files
```

```python
# Custom dataset class
from litgpt.data import LitDataModule

class MyData(LitDataModule):
    def prepare_data(self):
        # Download / process
        pass
    def train_dataloader(self):
        # Return DataLoader
        pass
```

## Pretraining from Scratch

```yaml
# pretrain_config.yaml
model_name: pythia-160m  # or define custom architecture

data:
  class_path: litgpt.data.TinyLlama  # or custom data module
  init_args:
    data_path: data/my_corpus

train:
  max_tokens: 10_000_000_000  # 10B tokens
  lr: 6e-4
  min_lr: 6e-5
  warmup_steps: 2000
  batch_size: 32
  micro_batch_size: 8
  max_seq_length: 2048
  weight_decay: 0.1
  beta1: 0.9
  beta2: 0.95

# Precision
precision: bf16-mixed
```

```bash
litgpt pretrain --config pretrain_config.yaml
```

## FSDP Multi-GPU Training

```bash
# Basic FSDP (all GPUs on one node)
litgpt finetune_lora meta-llama/Llama-3.1-8B-Instruct \
    --devices 4 \
    --data JSON --data.json_path data.json

# Full FSDP for full finetuning
litgpt finetune meta-llama/Llama-3.1-8B-Instruct \
    --devices 4 \
    --strategy fsdp \
    --precision bf16-mixed

# Multi-node
litgpt finetune --devices 8 --num_nodes 2 --strategy fsdp
```

## Converting Checkpoints

```bash
# LitGPT -> HuggingFace (for sharing / evaluation)
litgpt convert_to_hf \
    checkpoints/meta-llama/Llama-3.1-8B-Instruct/lora-finetuned \
    out/hf-checkpoint

# HuggingFace -> LitGPT (for training)
litgpt convert_from_hf \
    meta-llama/Llama-3.1-8B \
    out/litgpt-checkpoint

# Merge LoRA weights into base model
litgpt merge_lora \
    checkpoints/meta-llama/Llama-3.1-8B-Instruct/lora-finetuned
```

## Supported Models (Partial List)

| Family | Models | Sizes |
|--------|--------|-------|
| LLaMA 3 | Llama-3.1, Llama-3.2 | 1B, 3B, 8B, 70B |
| Mistral | Mistral, Mixtral | 7B, 8x7B |
| Qwen | Qwen2, Qwen2.5 | 0.5B - 72B |
| Gemma | Gemma, Gemma2 | 2B, 7B, 9B, 27B |
| Phi | Phi-3, Phi-3.5 | 3.8B, 4.2B |
| Pythia | Pythia | 70M - 12B |
| StableLM | StableLM | 3B, 7B |

## Memory Estimates

| Model Size | Full Finetune | LoRA | QLoRA |
|------------|---------------|------|-------|
| 1B | 8GB | 6GB | 4GB |
| 7B | 48GB | 24GB | 12GB |
| 13B | 80GB | 40GB | 24GB |
| 70B | 8xA100 | 2xA100 | 48GB |

## Tips for Research

- Use `litgpt pretrain` with a small model config to iterate on architecture ideas
- LoRA rank 16-32 is usually sufficient; higher ranks rarely help
- Always convert to HuggingFace format for evaluation with lm-eval-harness
- Use `--precision bf16-mixed` on Ampere+ GPUs, `--precision 16-mixed` on older
- Check `litgpt/config.py` for all model architecture parameters
