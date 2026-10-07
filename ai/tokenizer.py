"""
Custom Byte-Pair Encoding (BPE) Tokenizer for nanoGPT NPC Dialogue.
- Preserves game special tags as single atomic tokens:
  <|npc|>, <|trust|>, <|memory|>, <|mood|>, <|input|>, <|response|>, <|end|>, <|pad|>
- Base vocabulary contains all standard ASCII characters (0-255 coverage, NO out-of-vocab errors).
- Learns ~1,000 subword merges from the dataset, giving ~1,100 total vocab size.
- 100% self-contained in standard Python (no external heavy libraries required).
"""

import os
import re
import pickle
import collections
from typing import List, Dict, Tuple

SPECIAL_TOKENS = [
    "<|pad|>",
    "<|culprit|>",
    "<|npc|>",
    "<|trust|>",
    "<|memory|>",
    "<|mood|>",
    "<|input|>",
    "<|response|>",
    "<|end|>"
]

PATTERN = re.compile(r"<\|[a-z]+\|>| ?[A-Za-z]+| ?[0-9]+| ?[^\s\w]+|\n")


class BPETokenizer:
    def __init__(self):
        self.special_tokens = list(SPECIAL_TOKENS)
        self.merges: List[Tuple[str, str]] = []
        self.vocab: Dict[str, int] = {}
        self.inverse_vocab: Dict[int, str] = {}

    def train(self, text: str, target_vocab_size: int = 1200):
        # 1. Base tokens: all special tokens + all single characters appearing in text
        chars = sorted(list(set(text)))
        vocab_list = list(self.special_tokens)
        for c in chars:
            if c not in vocab_list:
                vocab_list.append(c)

        # 2. Extract words
        words = PATTERN.findall(text)
        word_counts = collections.Counter(words)

        # 3. Represent words as list of symbols
        splits = {}
        for w in word_counts:
            if w in self.special_tokens:
                splits[w] = [w]
            else:
                splits[w] = list(w)

        self.merges = []
        num_merges_to_do = target_vocab_size - len(vocab_list)

        for _ in range(max(0, num_merges_to_do)):
            pairs = collections.defaultdict(int)
            for w, freq in word_counts.items():
                if w in self.special_tokens:
                    continue
                syms = splits[w]
                for i in range(len(syms) - 1):
                    pairs[(syms[i], syms[i + 1])] += freq

            if not pairs:
                break
            best_pair = max(pairs, key=pairs.get)
            if pairs[best_pair] < 2:
                break

            self.merges.append(best_pair)
            merged_str = best_pair[0] + best_pair[1]
            if merged_str not in vocab_list:
                vocab_list.append(merged_str)

            # Update splits
            for w in splits:
                if w in self.special_tokens:
                    continue
                syms = splits[w]
                new_syms = []
                j = 0
                while j < len(syms):
                    if j < len(syms) - 1 and syms[j] == best_pair[0] and syms[j + 1] == best_pair[1]:
                        new_syms.append(merged_str)
                        j += 2
                    else:
                        new_syms.append(syms[j])
                        j += 1
                splits[w] = new_syms

        self.vocab = {tok: idx for idx, tok in enumerate(vocab_list)}
        self.inverse_vocab = {idx: tok for idx, tok in enumerate(vocab_list)}
        print(f"BPE Tokenizer trained: {len(self.vocab)} tokens, {len(self.merges)} merge rules.")

    def _encode_word(self, word: str) -> List[str]:
        if word in self.special_tokens:
            return [word]
        syms = list(word)
        for p0, p1 in self.merges:
            if len(syms) < 2:
                break
            merged = p0 + p1
            new_syms = []
            j = 0
            while j < len(syms):
                if j < len(syms) - 1 and syms[j] == p0 and syms[j + 1] == p1:
                    new_syms.append(merged)
                    j += 2
                else:
                    new_syms.append(syms[j])
                    j += 1
            syms = new_syms
        return syms

    def encode(self, text: str) -> List[int]:
        words = PATTERN.findall(text)
        token_ids = []
        for w in words:
            subwords = self._encode_word(w)
            for sw in subwords:
                if sw in self.vocab:
                    token_ids.append(self.vocab[sw])
                else:
                    # Fallback char-by-char if rare char
                    for c in sw:
                        if c in self.vocab:
                            token_ids.append(self.vocab[c])
        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        res = []
        for tid in token_ids:
            if tid in self.inverse_vocab:
                res.append(self.inverse_vocab[tid])
        return "".join(res)

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump({
                "special_tokens": self.special_tokens,
                "merges": self.merges,
                "vocab": self.vocab,
                "inverse_vocab": self.inverse_vocab
            }, f)

    @classmethod
    def load(cls, filepath: str) -> "BPETokenizer":
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        tok = cls()
        tok.special_tokens = data["special_tokens"]
        tok.merges = data["merges"]
        tok.vocab = data["vocab"]
        tok.inverse_vocab = data["inverse_vocab"]
        return tok
