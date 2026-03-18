"""Training script for all depth-aggregation methods.

Usage:
    python -m src.train --config configs/prenorm.yaml
    python -m src.train --config configs/block_attnres.yaml
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from datetime import datetime
from pathlib import Path

import torch
import torch.nn.functional as F

from .utils.seed import set_seed
from .utils.config import load_config
from .models.factory import create_model
from .data.fineweb import create_dataloader


def get_lr(step: int, warmup_steps: int, total_steps: int,
           peak_lr: float, min_lr: float) -> float:
    """Cosine learning rate schedule with warmup."""
    if step < warmup_steps:
        return peak_lr * step / warmup_steps
    if step >= total_steps:
        return min_lr
    progress = (step - warmup_steps) / (total_steps - warmup_steps)
    return min_lr + 0.5 * (peak_lr - min_lr) * (1 + math.cos(math.pi * progress))


def train(config_path: str):
    model_cfg, train_cfg = load_config(config_path)
    set_seed(train_cfg.seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if train_cfg.precision == "bf16" else torch.float16

    # Create output dirs
    method = model_cfg.method
    run_dir = Path(train_cfg.output_dir) / method
    ckpt_dir = Path(train_cfg.checkpoint_dir) / method
    run_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # Model
    model = create_model(model_cfg)
    model = model.to(device)
    params = model.count_parameters()
    print(f"[{method}] Parameters: {params['total']:,} total, {params['non_embedding']:,} non-embedding")

    if train_cfg.compile_model and hasattr(torch, "compile"):
        model = torch.compile(model)

    # Optimizer
    param_groups = [
        {"params": [p for n, p in model.named_parameters() if p.dim() >= 2], "weight_decay": train_cfg.weight_decay},
        {"params": [p for n, p in model.named_parameters() if p.dim() < 2], "weight_decay": 0.0},
    ]
    optimizer = torch.optim.AdamW(
        param_groups,
        lr=train_cfg.peak_lr,
        betas=(train_cfg.beta1, train_cfg.beta2),
        fused=device == "cuda",
    )

    # Data
    train_loader = create_dataloader(
        dataset_name=train_cfg.dataset,
        subset=train_cfg.dataset_subset,
        tokenizer_name=train_cfg.tokenizer,
        seq_len=train_cfg.seq_len,
        batch_size=train_cfg.micro_batch_size,
        seed=train_cfg.seed,
        num_workers=train_cfg.num_workers,
    )
    val_loader = create_dataloader(
        dataset_name=train_cfg.dataset,
        subset=train_cfg.dataset_subset,
        split="train",  # Use a different seed for val split
        tokenizer_name=train_cfg.tokenizer,
        seq_len=train_cfg.seq_len,
        batch_size=train_cfg.micro_batch_size,
        seed=train_cfg.seed + 1,
        max_tokens=train_cfg.val_tokens,
        num_workers=0,
    )

    grad_accum = train_cfg.grad_accum_steps
    total_steps = train_cfg.total_steps
    scaler = torch.amp.GradScaler(enabled=(dtype == torch.float16))

    # Logging - protect existing results
    log_file = run_dir / "train_log.jsonl"
    metrics_file = run_dir / "metrics.json"
    best_val_ppl = float("inf")

    # Guard: if metrics.json already exists with valid results, skip training
    if metrics_file.exists():
        try:
            existing = json.loads(metrics_file.read_text())
            if existing.get("best_val_ppl") and existing["best_val_ppl"] < float("inf"):
                print(f"[{method}] metrics.json already exists with valid results. Skipping.")
                return
        except (json.JSONDecodeError, KeyError):
            pass  # invalid metrics, re-run

    # Guard: if log file has content, back it up before overwriting
    if log_file.exists() and log_file.stat().st_size > 0:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = run_dir / f"train_log_{ts}.jsonl"
        log_file.rename(backup)
        print(f"[{method}] Backed up existing log to {backup.name}")

    val_log = run_dir / "val_log.jsonl"
    if val_log.exists() and val_log.stat().st_size > 0:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = run_dir / f"val_log_{ts}.jsonl"
        val_log.rename(backup)

    print(f"[{method}] Training: {total_steps} steps, {grad_accum} grad accum, "
          f"batch={train_cfg.batch_size_tokens} tokens")

    # Training loop
    model.train()
    train_iter = iter(train_loader)
    step = 0
    tokens_seen = 0
    t0 = time.time()

    while step < total_steps:
        optimizer.zero_grad()
        step_loss = 0.0

        for micro_step in range(grad_accum):
            try:
                batch = next(train_iter)
            except StopIteration:
                train_iter = iter(train_loader)
                batch = next(train_iter)

            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            with torch.amp.autocast(device_type=device, dtype=dtype):
                logits = model(input_ids)
                loss = F.cross_entropy(
                    logits.view(-1, logits.size(-1)),
                    labels.view(-1),
                )
                loss = loss / grad_accum

            scaler.scale(loss).backward()
            step_loss += loss.item()
            tokens_seen += input_ids.numel()

        # Gradient clipping
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)

        # LR schedule
        lr = get_lr(step, train_cfg.warmup_steps, total_steps,
                     train_cfg.peak_lr, train_cfg.min_lr)
        for pg in optimizer.param_groups:
            pg["lr"] = lr

        scaler.step(optimizer)
        scaler.update()
        step += 1

        # Logging
        if step % train_cfg.log_interval == 0:
            elapsed = time.time() - t0
            tps = tokens_seen / elapsed
            ppl = math.exp(step_loss)
            entry = {
                "step": step,
                "loss": round(step_loss, 4),
                "ppl": round(ppl, 2),
                "lr": round(lr, 6),
                "tokens": tokens_seen,
                "tps": round(tps, 0),
                "elapsed_s": round(elapsed, 1),
            }
            print(f"  step {step}/{total_steps} | loss={step_loss:.4f} ppl={ppl:.2f} | "
                  f"lr={lr:.2e} | {tps:.0f} tok/s")
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Validation
        if step % train_cfg.val_interval == 0:
            model.eval()
            val_loss_sum = 0.0
            val_tokens = 0
            with torch.no_grad():
                for val_batch in val_loader:
                    input_ids = val_batch["input_ids"].to(device)
                    labels = val_batch["labels"].to(device)
                    with torch.amp.autocast(device_type=device, dtype=dtype):
                        logits = model(input_ids)
                        loss = F.cross_entropy(
                            logits.view(-1, logits.size(-1)),
                            labels.view(-1),
                            reduction="sum",
                        )
                    val_loss_sum += loss.item()
                    val_tokens += labels.numel()

            val_loss = val_loss_sum / max(val_tokens, 1)
            val_ppl = math.exp(val_loss)
            print(f"  [VAL] step {step} | val_loss={val_loss:.4f} val_ppl={val_ppl:.2f}")

            val_entry = {"step": step, "val_loss": round(val_loss, 4),
                         "val_ppl": round(val_ppl, 2), "tokens": tokens_seen}
            with open(run_dir / "val_log.jsonl", "a") as f:
                f.write(json.dumps(val_entry) + "\n")

            if val_ppl < best_val_ppl:
                best_val_ppl = val_ppl
                torch.save(model.state_dict(), ckpt_dir / "best.pt")

            # Recreate val loader (streaming doesn't support reset)
            val_loader = create_dataloader(
                dataset_name=train_cfg.dataset,
                subset=train_cfg.dataset_subset,
                split="train",
                tokenizer_name=train_cfg.tokenizer,
                seq_len=train_cfg.seq_len,
                batch_size=train_cfg.micro_batch_size,
                seed=train_cfg.seed + 1,
                max_tokens=train_cfg.val_tokens,
                num_workers=0,
            )
            model.train()

        # Checkpoint
        if step % train_cfg.save_interval == 0:
            torch.save({
                "step": step,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "tokens_seen": tokens_seen,
                "best_val_ppl": best_val_ppl,
            }, ckpt_dir / f"step_{step}.pt")

    # Final save
    torch.save(model.state_dict(), ckpt_dir / "final.pt")

    # Save final metrics
    final_metrics = {
        "method": method,
        "total_steps": step,
        "tokens_seen": tokens_seen,
        "best_val_ppl": best_val_ppl,
        "total_time_s": round(time.time() - t0, 1),
        "parameters": params,
        "peak_vram_mb": round(torch.cuda.max_memory_allocated() / 1e6, 1) if torch.cuda.is_available() else 0,
    }
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"\n[{method}] Training complete. Best val PPL: {best_val_ppl:.2f}")
    return final_metrics


def main():
    parser = argparse.ArgumentParser(description="Train depth-aggregation models")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config")
    args = parser.parse_args()
    train(args.config)


if __name__ == "__main__":
    main()
