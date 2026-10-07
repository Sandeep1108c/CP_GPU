"""
Line-aware, Prompt-Masked Data Preparation for nanoGPT Dialogue Training.
Pads each dialogue turn cleanly so characters NEVER bleed into each other.
"""

import os
import sys
import pickle
import numpy as np

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(DATA_DIR, "data", "training_data_master.txt")
OUTPUT_DIR = os.path.join(DATA_DIR, "data")
BLOCK_SIZE = 160 # 99.8% of dialogue lines fit in 160 tokens

sys.path.insert(0, DATA_DIR)
from tokenizer import BPETokenizer


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"Total dialogue turns: {len(lines):,}")

    tokenizer = BPETokenizer()
    tokenizer.train("\n".join(lines), target_vocab_size=1200)

    tok_path = os.path.join(OUTPUT_DIR, "bpe_tokenizer.pkl")
    tokenizer.save(tok_path)
    print(f"Saved tokenizer to {tok_path}")

    pad_id = tokenizer.vocab["<|pad|>"]
    resp_tag_id = tokenizer.vocab["<|response|>"]

    # Build (N, BLOCK_SIZE) input arrays and target arrays
    all_x = []
    all_y = []

    for line in lines:
        tokens = tokenizer.encode(line)
        if len(tokens) > BLOCK_SIZE:
            tokens = tokens[:BLOCK_SIZE]

        # Targets: -1 for prompt tokens, only train on tokens AFTER <|response|>
        x = tokens[:-1]
        y = tokens[1:]

        # Find position of <|response|> in tokens
        if resp_tag_id in x:
            resp_idx = x.index(resp_tag_id)
            # Mask out prompt from loss
            target = [-1] * len(y)
            for j in range(resp_idx, len(y)):
                target[j] = y[j]
        else:
            target = list(y)

        # Pad to BLOCK_SIZE - 1
        pad_len = (BLOCK_SIZE - 1) - len(x)
        x = x + [pad_id] * pad_len
        target = target + [-1] * pad_len

        all_x.append(x)
        all_y.append(target)

    all_x = np.array(all_x, dtype=np.int64)
    all_y = np.array(all_y, dtype=np.int64)

    # Shuffle
    indices = np.random.permutation(len(all_x))
    all_x = all_x[indices]
    all_y = all_y[indices]

    # Split 95/5 to maximize training data exposure
    n = len(all_x)
    split_idx = int(n * 0.95)

    train_x, train_y = all_x[:split_idx], all_y[:split_idx]
    val_x, val_y = all_x[split_idx:], all_y[split_idx:]

    print(f"Train samples: {len(train_x):,} | Val samples: {len(val_x):,}")
    print(f"Matrix shape: {train_x.shape}")

    np.save(os.path.join(OUTPUT_DIR, "train_x.npy"), train_x)
    np.save(os.path.join(OUTPUT_DIR, "train_y.npy"), train_y)
    np.save(os.path.join(OUTPUT_DIR, "val_x.npy"), val_x)
    np.save(os.path.join(OUTPUT_DIR, "val_y.npy"), val_y)

    meta = {
        "vocab_size": len(tokenizer.vocab),
        "itos": tokenizer.inverse_vocab,
        "stoi": tokenizer.vocab,
        "block_size": BLOCK_SIZE,
        "tokenizer_type": "bpe"
    }
    with open(os.path.join(OUTPUT_DIR, "meta.pkl"), "wb") as f:
        pickle.dump(meta, f)

    print(f"Clean masked tensors saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
