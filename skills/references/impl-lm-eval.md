# lm-evaluation-harness Implementation Patterns
> Reference for S5. Load when running standardized benchmarks for model evaluation.
> Source: Adapted from [Orchestra Research AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

## When to Use

- Standardized evaluation in S5 (Analysis stage)
- Comparing against published baselines
- Reproducible benchmark results
- Need consistent evaluation across model variants

## Setup

```bash
pip install lm-eval
# or from source (for latest tasks)
git clone https://github.com/EleutherAI/lm-evaluation-harness.git
cd lm-evaluation-harness && pip install -e ".[all]"
```

## Quick Start

```bash
# Evaluate a HuggingFace model on MMLU
lm_eval --model hf \
    --model_args pretrained=meta-llama/Llama-3.1-8B-Instruct \
    --tasks mmlu \
    --num_fewshot 5 \
    --batch_size auto \
    --output_path results/

# Multiple tasks at once
lm_eval --model hf \
    --model_args pretrained=my-model \
    --tasks mmlu,gsm8k,hellaswag,arc_challenge \
    --batch_size auto \
    --output_path results/
```

## Key Benchmarks

| Benchmark | What it Tests | Few-shot | Metric | Time (7B) |
|-----------|---------------|----------|--------|-----------|
| `mmlu` | World knowledge (57 subjects) | 5 | acc | ~2 hrs |
| `gsm8k` | Math reasoning | 5 | exact_match | ~30 min |
| `hellaswag` | Commonsense reasoning | 10 | acc_norm | ~10 min |
| `truthfulqa_mc2` | Truthfulness | 0 | acc | ~5 min |
| `arc_challenge` | Science reasoning | 25 | acc_norm | ~15 min |
| `winogrande` | Coreference resolution | 5 | acc | ~5 min |
| `humaneval` | Code generation | 0 | pass@1 | ~20 min |
| `mbpp` | Code generation | 3 | pass@1 | ~30 min |
| `ifeval` | Instruction following | 0 | multiple | ~10 min |

## Common Command Patterns

### HuggingFace Model (Local or Hub)

```bash
# From HuggingFace Hub
lm_eval --model hf \
    --model_args pretrained=Qwen/Qwen2.5-7B-Instruct \
    --tasks mmlu,gsm8k \
    --num_fewshot 5 \
    --batch_size auto \
    --output_path results/qwen-7b/

# Local checkpoint
lm_eval --model hf \
    --model_args pretrained=./checkpoints/my-model \
    --tasks mmlu \
    --batch_size auto

# With quantization
lm_eval --model hf \
    --model_args pretrained=my-model,load_in_4bit=True \
    --tasks mmlu \
    --batch_size auto

# With specific dtype
lm_eval --model hf \
    --model_args pretrained=my-model,dtype=bfloat16 \
    --tasks mmlu \
    --batch_size auto

# With LoRA adapter
lm_eval --model hf \
    --model_args pretrained=base-model,peft=./lora-adapter \
    --tasks mmlu \
    --batch_size auto
```

### vLLM Backend (5-10x Faster)

```bash
# vLLM for fast inference (recommended for large evaluations)
lm_eval --model vllm \
    --model_args pretrained=meta-llama/Llama-3.1-8B-Instruct,tensor_parallel_size=1 \
    --tasks mmlu,gsm8k,hellaswag,arc_challenge \
    --batch_size auto \
    --output_path results/

# Multi-GPU with vLLM
lm_eval --model vllm \
    --model_args pretrained=meta-llama/Llama-3.1-70B-Instruct,tensor_parallel_size=4 \
    --tasks mmlu \
    --batch_size auto

# vLLM with max model length
lm_eval --model vllm \
    --model_args pretrained=my-model,max_model_len=4096 \
    --tasks gsm8k
```

### Chat/Instruct Models

```bash
# Apply chat template automatically
lm_eval --model hf \
    --model_args pretrained=my-instruct-model \
    --tasks mmlu \
    --apply_chat_template \
    --num_fewshot 5
```

## Saving and Parsing Results

```bash
# Results saved as JSON
lm_eval --model hf \
    --model_args pretrained=my-model \
    --tasks mmlu,gsm8k \
    --output_path results/ \
    --log_samples  # Save individual predictions

# Results structure:
# results/
#   my-model/
#     results_*.json     # Aggregate scores
#     samples_*.jsonl    # Individual predictions (if --log_samples)
```

### Parsing Results in Python

```python
import json
from pathlib import Path

def load_results(results_dir):
    """Load lm-eval results from output directory."""
    results = {}
    for f in Path(results_dir).glob("results_*.json"):
        with open(f) as fp:
            data = json.load(fp)
            for task, metrics in data["results"].items():
                results[task] = {
                    k: v for k, v in metrics.items()
                    if not k.startswith("_")
                }
    return results

# Example output:
# {"mmlu": {"acc": 0.654, "acc_stderr": 0.003},
#  "gsm8k": {"exact_match": 0.523, "exact_match_stderr": 0.014}}
```

## Hardware Estimates

| Model Size | Backend | MMLU | GSM8K | Full Suite (6 tasks) |
|------------|---------|------|-------|---------------------|
| 1.5B | HF | 30 min | 10 min | 1 hr |
| 7B | HF | 2 hrs | 30 min | 4 hrs |
| 7B | vLLM | 20 min | 5 min | 40 min |
| 13B | HF | 4 hrs | 1 hr | 8 hrs |
| 13B | vLLM | 40 min | 10 min | 1.5 hrs |
| 70B | vLLM (4xA100) | 1 hr | 15 min | 2 hrs |

## Custom Task

```yaml
# my_task.yaml
task: my_custom_task
dataset_path: json
dataset_name: null
dataset_kwargs:
  data_files: test.jsonl
output_type: generate_until
generation_kwargs:
  max_gen_toks: 512
  temperature: 0.0
doc_to_text: "Question: {{question}}\nAnswer:"
doc_to_target: "{{answer}}"
metric_list:
  - metric: exact_match
    aggregation: mean
    higher_is_better: true
```

```bash
# Run custom task
lm_eval --model hf \
    --model_args pretrained=my-model \
    --tasks my_custom_task \
    --include_path ./my_tasks/
```

## Comparing Models (Research Table)

```bash
# Run same tasks across all model variants
for model in base-model sft-model dpo-model grpo-model; do
    lm_eval --model vllm \
        --model_args pretrained=./checkpoints/$model \
        --tasks mmlu,gsm8k,hellaswag,arc_challenge,truthfulqa_mc2,winogrande \
        --batch_size auto \
        --output_path results/$model/
done
```

```python
# Generate comparison table
import pandas as pd

models = ["base-model", "sft-model", "dpo-model", "grpo-model"]
tasks = ["mmlu", "gsm8k", "hellaswag", "arc_challenge"]

rows = []
for model in models:
    results = load_results(f"results/{model}/")
    row = {"Model": model}
    for task in tasks:
        key = "acc" if task != "gsm8k" else "exact_match"
        row[task] = f"{results[task][key]*100:.1f}"
    rows.append(row)

df = pd.DataFrame(rows)
print(df.to_markdown(index=False))
# | Model | mmlu | gsm8k | hellaswag | arc_challenge |
```

## Tips

- Always use `--batch_size auto` to maximize throughput
- Use vLLM backend for evaluations that take > 30 minutes
- Run `--limit 100` first to sanity-check before full evaluation
- `--num_fewshot` should match published baselines for fair comparison
- For generative tasks (gsm8k, humaneval), temperature=0 for reproducibility
- Save results JSON for paper tables and reproducibility
