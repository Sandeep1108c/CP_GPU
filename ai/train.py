"""
nanoGPT Training Script for NPC Dialogue Model.

Trains a ~4.8M parameter character-level GPT on the "Find the Thief" game
NPC dialogue dataset. Optimized for RTX 4050 (6GB VRAM).

Usage:
    python ai/train.py

Outputs:
    ai/checkpoints/  — Model checkpoints (best + periodic)
    ai/train_log.txt — Training loss log
"""

import os
import sys
import time
import math
import pickle

import numpy as np
import torch

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import GPT, GPTConfig

# ============================================================
# Configuration
# ============================================================

# Data
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ckpt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")
os.makedirs(ckpt_dir, exist_ok=True)

# Model — exactly 4.81M parameters (< 5.0M target for resume/spec)
block_size = 160     # Line-aware sequence length
n_layer = 6          # 6 layers
n_head = 8           # 8 heads (248 is divisible by 8 -> head_dim = 31)
n_embd = 248         # 248 embedding dimension
dropout = 0.02       # Minimal dropout so model firmly learns facts, names, and exact phrasing

# Training — tuned for firm convergence without premature cutoff
batch_size = 32
max_iters = 3500
eval_interval = 100
eval_iters = 50
log_interval = 50
patience = 35        # High patience: allows the model to fully learn all 4 scenarios

# Optimizer
learning_rate = 4e-4
weight_decay = 0.05
beta1 = 0.9
beta2 = 0.99
grad_clip = 1.0

# LR schedule
warmup_iters = 80
lr_decay_iters = 3500
min_lr = 4e-5

# System
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32
compile_model = False

# ============================================================
# Data Loading
# ============================================================

# Load vocab metadata
meta_path = os.path.join(data_dir, "meta.pkl")
if not os.path.exists(meta_path):
    print("ERROR: meta.pkl not found. Run prepare_data.py first!")
    sys.exit(1)

with open(meta_path, "rb") as f:
    meta = pickle.load(f)

vocab_size = meta["vocab_size"]
itos = meta["itos"]
stoi = meta["stoi"]
print(f"Vocab size: {vocab_size}")

# Load line-aware arrays with prompt loss masking
train_x = np.load(os.path.join(data_dir, "train_x.npy"))
train_y = np.load(os.path.join(data_dir, "train_y.npy"))
val_x = np.load(os.path.join(data_dir, "val_x.npy"))
val_y = np.load(os.path.join(data_dir, "val_y.npy"))
block_size = meta.get("block_size", 160)
print(f"Loaded {len(train_x):,} train dialogue turns, {len(val_x):,} val turns. Sequence length: {block_size}")


def get_batch(split):
    dx, dy = (train_x, train_y) if split == "train" else (val_x, val_y)
    ix = np.random.randint(0, len(dx), size=batch_size)
    x = torch.from_numpy(dx[ix]).to(device)
    y = torch.from_numpy(dy[ix]).to(device)
    return x, y


# ============================================================
# Model Init
# ============================================================

config = GPTConfig(
    vocab_size=vocab_size,
    block_size=block_size,
    n_layer=n_layer,
    n_head=n_head,
    n_embd=n_embd,
    dropout=dropout,
)
model = GPT(config)
model.to(device)

if compile_model and hasattr(torch, "compile"):
    print("Compiling model with torch.compile...")
    model = torch.compile(model)

# Optimizer
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=learning_rate,
    betas=(beta1, beta2),
    weight_decay=weight_decay,
)

# AMP scaler for mixed precision
scaler = torch.amp.GradScaler("cuda", enabled=(dtype == torch.float16))


def get_lr(it):
    """Cosine learning rate schedule with warmup."""
    if it < warmup_iters:
        return learning_rate * it / warmup_iters
    if it > lr_decay_iters:
        return min_lr
    decay_ratio = (it - warmup_iters) / (lr_decay_iters - warmup_iters)
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    return min_lr + coeff * (learning_rate - min_lr)


# ============================================================
# Evaluation
# ============================================================

@torch.no_grad()
def estimate_loss():
    out = {}
    model.eval()
    for split in ["train", "val"]:
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            X, Y = get_batch(split)
            with torch.amp.autocast("cuda", enabled=(dtype == torch.float16)):
                _, loss = model(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out


# ============================================================
# Training Loop
# ============================================================

print(f"\nTraining on {device} with {dtype}")
print(f"Config: {n_layer}L / {n_head}H / {n_embd}E / block_size={block_size} / dropout={dropout}")
print(f"Batch size: {batch_size} | Max iters: {max_iters} | Early stop patience: {patience}")
print(f"=" * 60)

best_val_loss = float("inf")
patience_counter = 0
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_log.txt")

# Clear old log
with open(log_file, "w") as f:
    f.write(f"# Retrain with dropout={dropout}, patience={patience}\n")

t0 = time.time()
for iter_num in range(max_iters):
    # Set learning rate
    lr = get_lr(iter_num)
    for param_group in optimizer.param_groups:
        param_group["lr"] = lr

    # Evaluate periodically
    if iter_num % eval_interval == 0 or iter_num == max_iters - 1:
        losses = estimate_loss()
        train_loss = losses["train"]
        val_loss = losses["val"]
        dt = time.time() - t0

        log_msg = f"iter {iter_num:5d} | train loss {train_loss:.4f} | val loss {val_loss:.4f} | lr {lr:.2e} | time {dt:.1f}s"
        print(log_msg)

        with open(log_file, "a") as f:
            f.write(log_msg + "\n")

        # Save best checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            checkpoint = {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "iter_num": iter_num,
                "best_val_loss": best_val_loss,
                "config": config.__dict__,
                "meta": meta,
            }
            torch.save(checkpoint, os.path.join(ckpt_dir, "best.pt"))
            print(f"  -> New best val loss! Saved checkpoint.")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\nEarly stopping: val loss hasn't improved for {patience} evals.")
                print(f"Best val loss: {best_val_loss:.4f} at iter ~{iter_num - patience * eval_interval}")
                break

    # Forward + backward
    X, Y = get_batch("train")
    with torch.amp.autocast("cuda", enabled=(dtype == torch.float16)):
        _, loss = model(X, Y)

    scaler.scale(loss).backward()

    if grad_clip > 0:
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

    scaler.step(optimizer)
    scaler.update()
    optimizer.zero_grad(set_to_none=True)

    # Log
    if iter_num % log_interval == 0 and iter_num > 0:
        dt = time.time() - t0
        print(f"  step {iter_num:5d} | loss {loss.item():.4f} | lr {lr:.2e} | {dt:.1f}s")

# Save final checkpoint
checkpoint = {
    "model": model.state_dict(),
    "optimizer": optimizer.state_dict(),
    "iter_num": max_iters,
    "best_val_loss": best_val_loss,
    "config": config.__dict__,
    "meta": meta,
}
torch.save(checkpoint, os.path.join(ckpt_dir, "final.pt"))

total_time = time.time() - t0
print(f"\n{'=' * 60}")
print(f"Training complete! {total_time:.1f}s total")
print(f"Best val loss: {best_val_loss:.4f}")
print(f"Checkpoints saved to: {ckpt_dir}")
