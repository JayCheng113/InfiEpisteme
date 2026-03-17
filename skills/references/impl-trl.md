# TRL Fine-Tuning Implementation Patterns
> Reference for S3/S4. Load when choosing between SFT, DPO, PPO, or GRPO training methods.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## Method Selection Guide

```
Do you have labeled input/output pairs?
├── YES → SFT (Supervised Fine-Tuning)
│         Done? Need alignment?
│         ├── Have preference pairs (chosen/rejected)? → DPO
│         ├── Have a reward model? → PPO
│         └── Have a reward function (no model)? → GRPO
└── NO
    ├── Have preference pairs? → DPO (can skip SFT)
    ├── Have reward function? → GRPO
    └── Have reward model? → PPO
```

| Method | Data Needed | Complexity | Memory | Best For |
|--------|------------|-----------|---------|----------|
| SFT | (input, output) pairs | Low | 16GB/7B | Teaching format, domain knowledge |
| DPO | (prompt, chosen, rejected) | Medium | 24GB/7B | Alignment with preference data |
| PPO | Reward model + prompts | High | 40GB/7B | Full RLHF pipeline |
| GRPO | Reward function + prompts | Medium | 24GB/7B | RL without preference data |

## Setup

```bash
pip install trl transformers datasets peft accelerate bitsandbytes
```

## SFT Quick Start

```python
from trl import SFTTrainer, SFTConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

dataset = load_dataset("json", data_files="train.jsonl")["train"]
# Format: [{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}]

config = SFTConfig(
    output_dir="./sft-output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    learning_rate=2e-5,
    warmup_ratio=0.1,
    bf16=True,
    logging_steps=10,
    save_steps=500,
    max_seq_length=2048,
)

trainer = SFTTrainer(
    model=model,
    args=config,
    train_dataset=dataset,
    processing_class=tokenizer,
)
trainer.train()
```

## DPO: Preference-Based Alignment

### Data Format

```python
# Each example needs: prompt, chosen, rejected
data = [
    {
        "prompt": [{"role": "user", "content": "Explain gravity"}],
        "chosen": [{"role": "assistant", "content": "Gravity is a fundamental force..."}],
        "rejected": [{"role": "assistant", "content": "Gravity is when stuff falls down"}],
    }
]
```

### DPO Training

```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(
    output_dir="./dpo-output",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-7,        # Lower LR than SFT
    beta=0.1,                  # KL penalty strength
    bf16=True,
    gradient_checkpointing=True,
    max_length=1024,
    max_prompt_length=512,
    logging_steps=10,
)

trainer = DPOTrainer(
    model=model,
    ref_model=None,           # None = use implicit reference (saves memory)
    args=config,
    train_dataset=dataset,
    processing_class=tokenizer,
)
trainer.train()
```

### Beta Tuning

| Beta | Effect | Use When |
|------|--------|----------|
| 0.01 | Weak KL penalty, model changes a lot | Strong preference signal |
| 0.1 | Default, balanced | Most cases |
| 0.5 | Strong KL penalty, conservative | Noisy preferences |

## PPO: Full RLHF Pipeline

```python
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead
from transformers import pipeline

# 1. Load model with value head
model = AutoModelForCausalLMWithValueHead.from_pretrained("my-sft-model")
ref_model = AutoModelForCausalLMWithValueHead.from_pretrained("my-sft-model")

# 2. Load reward model
reward_pipe = pipeline("text-classification", model="reward-model", device=0)

# 3. Configure PPO
config = PPOConfig(
    output_dir="./ppo-output",
    learning_rate=1e-6,
    batch_size=16,
    mini_batch_size=4,
    gradient_accumulation_steps=4,
    ppo_epochs=4,
    max_grad_norm=0.5,
)

trainer = PPOTrainer(
    config=config,
    model=model,
    ref_model=ref_model,
    processing_class=tokenizer,
)

# 4. Training loop
for batch in dataloader:
    queries = batch["input_ids"]
    responses = trainer.generate(queries, max_new_tokens=256)

    # Score with reward model
    texts = [tokenizer.decode(r) for r in responses]
    rewards = [torch.tensor(reward_pipe(t)[0]["score"]) for t in texts]

    stats = trainer.step(queries, responses, rewards)
```

## Hardware Requirements

| Method | 1.5B | 7B | 13B | 70B |
|--------|------|-----|------|------|
| SFT (full) | 8GB | 32GB | 60GB | 4xA100 |
| SFT (LoRA) | 4GB | 16GB | 24GB | 48GB |
| DPO (full) | 16GB | 48GB | 80GB | 8xA100 |
| DPO (LoRA) | 8GB | 24GB | 40GB | 80GB |
| PPO | 16GB | 40GB | 80GB | 8xA100 |
| GRPO (LoRA) | 8GB | 24GB | 40GB | 80GB |

## Memory Optimization

### LoRA/QLoRA (All Methods)

```python
from peft import LoraConfig

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

# For QLoRA (4-bit), load model in 4-bit first
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    model_name, quantization_config=bnb_config
)

# Pass peft_config to any trainer
trainer = SFTTrainer(..., peft_config=peft_config)
trainer = DPOTrainer(..., peft_config=peft_config)
trainer = GRPOTrainer(..., peft_config=peft_config)
```

### Gradient Checkpointing

```python
# Add to any config
config = SFTConfig(
    ...,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
)
```

### Multi-GPU with DeepSpeed

```bash
# ds_config.json
{
    "bf16": {"enabled": true},
    "zero_optimization": {
        "stage": 2,
        "offload_optimizer": {"device": "cpu"}
    }
}

# Launch
accelerate launch --config_file ds_config.yaml train.py
```

## Typical Training Pipeline

```bash
# Stage 1: SFT
python sft.py --model base-model --data sft_data.jsonl --epochs 3

# Stage 2: DPO (on SFT checkpoint)
python dpo.py --model sft-checkpoint --data preference_data.jsonl --epochs 1

# Stage 3: Evaluate
lm_eval --model hf --model_args pretrained=dpo-checkpoint --tasks mmlu,gsm8k
```

## Tips

- Always SFT before DPO/PPO (the model needs to be able to follow instructions first)
- DPO `beta=0.1` is a safe default; tune if reward hacking occurs
- PPO is most powerful but hardest to stabilize; try DPO or GRPO first
- For GRPO details, see `impl-trl-grpo.md`
- Save checkpoints frequently; RL training can be unstable
- Monitor reward AND KL divergence; reward up + KL exploding = reward hacking
