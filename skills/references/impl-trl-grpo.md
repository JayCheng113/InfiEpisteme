# TRL GRPO Implementation Patterns
> Reference for S3/S4. Load when doing reward-based RL training without preference data.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- Alignment without paired preference data (no need for chosen/rejected pairs)
- Reward-based optimization (you have a reward function, not human labels)
- Reasoning improvement (math, code, logic tasks)
- Format/style enforcement via reward shaping
- DeepSeek-R1 style training

## Core Concept

GRPO generates **multiple completions per prompt**, scores them with a reward function, and uses **group-relative advantage** to update the policy. No critic/value model needed.

```
Prompt → Generate N completions → Score each → Normalize within group → Policy gradient
```

## Minimal GRPO Example

```python
from trl import GRPOTrainer, GRPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
tokenizer.pad_token = tokenizer.eos_token

# Reward function: receives list of completions, returns list of floats
def reward_fn(completions, **kwargs):
    """Score each completion. Higher = better."""
    rewards = []
    for completion in completions:
        text = completion[0]["content"]
        # Example: reward correct answer format
        if "<answer>" in text and "</answer>" in text:
            rewards.append(1.0)
        else:
            rewards.append(-1.0)
    return rewards

config = GRPOConfig(
    output_dir="./grpo-output",
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=8,          # completions per prompt
    max_completion_length=512,
    max_prompt_length=256,
    learning_rate=5e-6,
    logging_steps=1,
    bf16=True,
)

trainer = GRPOTrainer(
    model=model,
    config=config,
    reward_funcs=reward_fn,
    train_dataset=dataset,  # must have "prompt" column
)
trainer.train()
```

## Reward Function Templates

### Correctness Reward (Math)

```python
import re

def correctness_reward(completions, ground_truth, **kwargs):
    rewards = []
    for completion, answer in zip(completions, ground_truth):
        text = completion[0]["content"]
        # Extract answer from \boxed{} or <answer> tags
        match = re.search(r'\\boxed\{(.+?)\}', text)
        if match and match.group(1).strip() == str(answer).strip():
            rewards.append(2.0)
        else:
            rewards.append(-1.0)
    return rewards
```

### Format Reward

```python
def format_reward(completions, **kwargs):
    """Reward structured thinking."""
    rewards = []
    for completion in completions:
        text = completion[0]["content"]
        score = 0.0
        if "<think>" in text and "</think>" in text:
            score += 0.5
        if "<answer>" in text and "</answer>" in text:
            score += 0.5
        rewards.append(score)
    return rewards
```

### Incremental Reward (Length/Detail)

```python
def length_reward(completions, **kwargs):
    """Reward longer, more detailed responses (capped)."""
    rewards = []
    for completion in completions:
        text = completion[0]["content"]
        word_count = len(text.split())
        # Reward up to 200 words, penalize beyond 500
        if word_count < 20:
            rewards.append(-1.0)
        elif word_count <= 200:
            rewards.append(word_count / 200.0)
        elif word_count <= 500:
            rewards.append(1.0)
        else:
            rewards.append(0.5)  # slight penalty for being too verbose
    return rewards
```

### Combining Multiple Rewards

```python
# Pass multiple reward functions as a list
trainer = GRPOTrainer(
    model=model,
    config=config,
    reward_funcs=[correctness_reward, format_reward],
    reward_weights=[2.0, 1.0],  # weight correctness higher
    train_dataset=dataset,
)
```

## GRPOConfig: Memory-Limited GPUs (24GB)

```python
config = GRPOConfig(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=8,
    max_completion_length=512,
    max_prompt_length=256,
    learning_rate=5e-6,
    bf16=True,
    gradient_checkpointing=True,
    use_vllm=False,       # vLLM needs extra GPU memory
    # Effective batch = 1 * 4 = 4 prompts, each with 8 generations
)
```

## GRPOConfig: Larger GPUs (48GB+ or multi-GPU)

```python
config = GRPOConfig(
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    num_generations=16,
    max_completion_length=1024,
    max_prompt_length=512,
    learning_rate=5e-6,
    bf16=True,
    use_vllm=True,         # 5-10x faster generation
    vllm_device="cuda:1",  # dedicate a GPU to vLLM
    vllm_gpu_memory_utilization=0.7,
)
```

## LoRA + GRPO Combo

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

trainer = GRPOTrainer(
    model=model,
    config=config,
    reward_funcs=reward_fn,
    train_dataset=dataset,
    peft_config=peft_config,  # adds LoRA automatically
)
```

## Unsloth Acceleration (2-3x Faster)

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
)

# Use with GRPOTrainer as normal
trainer = GRPOTrainer(model=model, config=config, ...)
```

## Dataset Format

```python
from datasets import Dataset

# Must have a "prompt" column (list of message dicts)
data = [
    {"prompt": [{"role": "user", "content": "What is 2+2?"}],
     "ground_truth": "4"},
    {"prompt": [{"role": "user", "content": "What is 3*5?"}],
     "ground_truth": "15"},
]
dataset = Dataset.from_list(data)
```

## Expected Loss Behavior

**IMPORTANT: Loss INCREASES during GRPO training. This is correct and expected.**

- GRPO maximizes reward, not minimizing cross-entropy loss
- The KL penalty term causes loss to rise as the model diverges from the reference
- Monitor **reward** (should increase) and **reward_std** (should decrease over time)
- A flat or decreasing reward with increasing loss = problem

## Multi-Stage Training Pattern

```
Stage 1: SFT on instruction data (standard supervised)
    ↓
Stage 2: GRPO with format reward only (learn structure)
    ↓
Stage 3: GRPO with correctness + format reward (learn accuracy)
    ↓
Stage 4: GRPO with all rewards (polish)
```

## Troubleshooting

### Mode Collapse (All Outputs Identical)
- Increase `temperature` in generation (default 1.0, try 1.2)
- Lower `learning_rate` (try 1e-6)
- Increase `num_generations` (more diversity per group)
- Add KL penalty: increase `beta` (default 0.04, try 0.1)

### OOM (Out of Memory)
- Reduce `num_generations` (8 → 4)
- Reduce `max_completion_length`
- Enable `gradient_checkpointing=True`
- Use LoRA + 4-bit quantization
- Use `use_vllm=True` with separate GPU for generation

### No Learning (Reward Flat)
- Check reward function returns varied scores (not all same)
- Ensure `num_generations` >= 4 (need variance for advantage estimation)
- Increase `learning_rate` (try 1e-5)
- Verify prompts are in correct chat template format
- Check that completions are actually different from each other

### NaN Loss
- Lower `learning_rate`
- Enable `max_grad_norm=1.0` (gradient clipping)
- Check reward function for extreme values (clip to [-5, 5])
