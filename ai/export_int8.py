"""
Export trained nanoGPT model to INT8 quantized format for ESP32-S3 inference.

Converts the trained PyTorch model to:
  1. Raw weight files (float32 → int8 with scale factors)
  2. C header file with model config for firmware integration

Usage:
    python ai/export_int8.py

Output:
    ai/export/  — INT8 weights + C header for ESP32 firmware
"""

import os
import sys
import struct
import pickle

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import GPT, GPTConfig

CKPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
os.makedirs(EXPORT_DIR, exist_ok=True)


def quantize_tensor(tensor, bits=8):
    """Symmetric per-tensor INT8 quantization."""
    t = tensor.float()
    scale = t.abs().max() / 127.0
    if scale == 0:
        scale = torch.tensor(1.0)
    quantized = torch.clamp(torch.round(t / scale), -128, 127).to(torch.int8)
    return quantized, scale.item()


def export_model():
    # Load converged checkpoint
    ckpt_path = os.path.join(CKPT_DIR, "final.pt")
    if not os.path.exists(ckpt_path):
        ckpt_path = os.path.join(CKPT_DIR, "best.pt")
    if not os.path.exists(ckpt_path):
        print("ERROR: No checkpoint found!")
        sys.exit(1)

    print(f"Loading: {ckpt_path}")
    checkpoint = torch.load(ckpt_path, map_location="cpu", weights_only=False)

    cfg = checkpoint["config"]
    meta = checkpoint["meta"]

    config = GPTConfig(
        vocab_size=cfg["vocab_size"],
        block_size=cfg["block_size"],
        n_layer=cfg["n_layer"],
        n_head=cfg["n_head"],
        n_embd=cfg["n_embd"],
    )

    model = GPT(config)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    print(f"Model: {config.n_layer}L / {config.n_head}H / {config.n_embd}E")
    print(f"Vocab: {config.vocab_size} | Block: {config.block_size}")

    # Export all weights as INT8
    total_bytes = 0
    scale_map = {}
    weights_file = os.path.join(EXPORT_DIR, "model_int8.bin")

    with open(weights_file, "wb") as f:
        # Write header: magic + config
        f.write(struct.pack("I", 0x4E475054))  # "NGPT" magic
        f.write(struct.pack("I", config.vocab_size))
        f.write(struct.pack("I", config.block_size))
        f.write(struct.pack("I", config.n_layer))
        f.write(struct.pack("I", config.n_head))
        f.write(struct.pack("I", config.n_embd))
        total_bytes += 24

        for name, param in model.named_parameters():
            q, scale = quantize_tensor(param.data)
            q_np = q.numpy().astype(np.int8)

            # Write: name_len, name, scale(float32), shape_dims, shape, data
            name_bytes = name.encode("utf-8")
            f.write(struct.pack("I", len(name_bytes)))
            f.write(name_bytes)
            f.write(struct.pack("f", scale))
            f.write(struct.pack("I", len(q_np.shape)))
            for dim in q_np.shape:
                f.write(struct.pack("I", dim))
            f.write(q_np.tobytes())

            param_bytes = q_np.nbytes
            total_bytes += 4 + len(name_bytes) + 4 + 4 + 4 * len(q_np.shape) + param_bytes
            scale_map[name] = scale

            print(f"  {name:50s} shape={str(list(q_np.shape)):20s} scale={scale:.6f}  ({param_bytes:,} bytes)")

    print(f"\nTotal INT8 model size: {total_bytes:,} bytes ({total_bytes/1e6:.2f} MB)")
    print(f"Saved to: {weights_file}")

    # Export vocabulary as C header
    itos = meta["itos"]
    stoi = meta["stoi"]

    header_path = os.path.join(EXPORT_DIR, "nanogpt_config.h")
    with open(header_path, "w") as f:
        f.write("// Auto-generated nanoGPT configuration for ESP32-S3\n")
        f.write(f"// Model: {config.n_layer}L / {config.n_head}H / {config.n_embd}E\n\n")
        f.write("#ifndef NANOGPT_CONFIG_H\n#define NANOGPT_CONFIG_H\n\n")
        f.write(f"#define NANOGPT_VOCAB_SIZE  {config.vocab_size}\n")
        f.write(f"#define NANOGPT_BLOCK_SIZE  {config.block_size}\n")
        f.write(f"#define NANOGPT_N_LAYER     {config.n_layer}\n")
        f.write(f"#define NANOGPT_N_HEAD      {config.n_head}\n")
        f.write(f"#define NANOGPT_N_EMBD      {config.n_embd}\n\n")

        # Vocab lookup tables as string array for BPE
        f.write("// Subword string to index mapping\n")
        f.write(f"static const char* const NANOGPT_VOCAB[{config.vocab_size}] = {{\n")
        for i in range(config.vocab_size):
            s = itos.get(i, "")
            # Escape string literal for C
            escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            f.write(f'    "{escaped}", // {i}\n')
        f.write("};\n\n")

        f.write("#endif // NANOGPT_CONFIG_H\n")

    print(f"C header saved to: {header_path}")


if __name__ == "__main__":
    export_model()
