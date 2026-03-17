# Unsloth Implementation Patterns
> Reference for S3/S4. Load when doing LoRA/QLoRA finetuning on single GPU and need speed/memory savings.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- LoRA/QLoRA finetuning on a single GPU
- Need 2-5x faster training than standard HuggingFace
- Memory-constrained (50-80% VRAM reduction)
- Compatible with TRL trainers (SFT, DPO, GRPO)
- Want 4-bit quantized training with minimal accuracy loss

## Setup

```bash
# For CUDA 12.1+
pip install unsloth
# or for specific CUDA version
pip install "unsloth[cu121]"
# or from source
pip install "unsloth @ git+https://github.com/unslothai/unsloth.git"
```

## Core Pattern

```python
from unsloth import FastLanguageModel

# 1. Load model with Unsloth (replaces AutoModelForCausalLM)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,       # QLoRA: 4-bit quantization
    dtype=None,              # Auto-detect (bf16 on Ampere+)
)

# 2. Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                    # LoRA rank
    lora_alpha=32,           # LoRA alpha (usually 2*r)
    lora_dropout=0,          # 0 is optimized by Unsloth
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",  # Unsloth's optimized checkpointing
    random_state=42,
)
```

## SFT with Unsloth + TRL

```python
from trl import SFTTrainer, SFTConfig

config = SFTConfig(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,        # Higher LR works with LoRA
    warmup_steps=100,
    bf16=True,
    logging_steps=10,
    save_steps=500,
    max_seq_length=2048,
    optim="adamw_8bit",        # 8-bit optimizer saves memory
    seed=42,
)

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    args=config,
    train_dataset=dataset,
)
trainer.train()
```

## DPO with Unsloth

```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(
    output_dir="./dpo-output",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-6,
    beta=0.1,
    bf16=True,
    gradient_checkpointing=True,
    max_length=1024,
    max_prompt_length=512,
    optim="adamw_8bit",
)

trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=config,
    train_dataset=dataset,
    processing_class=tokenizer,
)
trainer.train()
```

## GRPO with Unsloth

```python
from trl import GRPOTrainer, GRPOConfig

config = GRPOConfig(
    output_dir="./grpo-output",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=8,
    max_completion_length=512,
    learning_rate=5e-6,
    bf16=True,
    optim="adamw_8bit",
)

trainer = GRPOTrainer(
    model=model,
    config=config,
    reward_funcs=my_reward_fn,
    train_dataset=dataset,
)
trainer.train()
```

## Saving and Loading

```python
# Save LoRA adapters only (small, fast)
model.save_pretrained("./lora-checkpoint")
tokenizer.save_pretrained("./lora-checkpoint")

# Save merged model (full weights, for deployment)
model.save_pretrained_merged("./merged-model", tokenizer)

# Save to GGUF (for llama.cpp / Ollama)
model.save_pretrained_gguf("./gguf-model", tokenizer, quantization_method="q4_k_m")

# Push to HuggingFace
model.push_to_hub_merged("username/my-model", tokenizer)

# Load saved LoRA
model, tokenizer = FastLanguageModel.from_pretrained("./lora-checkpoint")
```

## Supported Models

| Family | Models | 4-bit VRAM (7B) |
|--------|--------|-----------------|
| LLaMA 3 | Llama-3.1, 3.2, 3.3 | ~5GB |
| Mistral | Mistral v0.3, Nemo | ~5GB |
| Gemma | Gemma 2, 3 | ~6GB |
| Qwen | Qwen2, Qwen2.5 | ~5GB |
| Phi | Phi-3, Phi-3.5, Phi-4 | ~4GB |
| DeepSeek | DeepSeek-R1 distills | ~5GB |

## Memory Comparison

| Setup | Standard HF | Unsloth | Savings |
|-------|------------|---------|---------|
| 7B LoRA fp16 | 18GB | 10GB | 44% |
| 7B QLoRA 4-bit | 10GB | 5GB | 50% |
| 13B QLoRA 4-bit | 18GB | 9GB | 50% |
| 7B SFT (bs=4) | 24GB | 12GB | 50% |

## Performance Tips

```python
# 1. Use Unsloth's gradient checkpointing (not PyTorch default)
use_gradient_checkpointing="unsloth"  # 30% less memory than standard

# 2. Use 8-bit optimizer
optim="adamw_8bit"  # Saves ~30% optimizer memory

# 3. LoRA dropout=0 is faster (Unsloth optimizes this case)
lora_dropout=0

# 4. Higher LoRA ranks are fine with Unsloth (memory overhead is minimal)
r=64  # Unsloth handles high rank efficiently

# 5. For inference after training
FastLanguageModel.for_inference(model)  # Enables 2x faster inference
output = model.generate(**inputs, max_new_tokens=256)
```

## Key Differences from Standard HF

| Standard HuggingFace | Unsloth |
|---------------------|---------|
| `AutoModelForCausalLM.from_pretrained()` | `FastLanguageModel.from_pretrained()` |
| `get_peft_model(model, config)` | `FastLanguageModel.get_peft_model(model, ...)` |
| `gradient_checkpointing=True` | `use_gradient_checkpointing="unsloth"` |
| `model.generate()` | `FastLanguageModel.for_inference(model)` then `model.generate()` |

## Limitations

- Single GPU only (no FSDP/DDP support)
- LoRA/QLoRA only (no full finetuning acceleration)
- Requires specific GPU architectures (CUDA, not AMD/Apple)
- Model must be in supported list (most popular models covered)
- For multi-GPU, use FSDP2 or TorchTitan instead
