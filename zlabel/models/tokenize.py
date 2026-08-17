"""Pure numpy CLIP SimpleTokenizer for the SAM3 text encoder (context_length=32)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import regex as re

CONTEXT_LENGTH = 32


def bytes_to_unicode() -> dict[int, str]:
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(2**8):
        if b not in bs:
            bs.append(b)
            cs.append(2**8 + n)
            n += 1
    return dict(zip(bs, (chr(c) for c in cs)))


def get_pairs(word: tuple) -> set:
    pairs = set()
    prev = word[0]
    for ch in word[1:]:
        pairs.add((prev, ch))
        prev = ch
    return pairs


class SimpleTokenizer:
    def __init__(self, vocab_path, merges_path):
        self.byte_encoder = bytes_to_unicode()
        self.byte_decoder = {v: k for k, v in self.byte_encoder.items()}
        with open(vocab_path, "r", encoding="utf-8") as f:
            self.encoder = json.load(f)
        self.decoder = {v: k for k, v in self.encoder.items()}
        with open(merges_path, "r", encoding="utf-8") as f:
            merges = f.read().split("\n")[1 : 49152 - 256 - 2 + 1]
        self.bpe_ranks = dict(zip([tuple(m.split()) for m in merges], range(len(merges))))
        self.cache = {
            "<|startoftext|>": "<|startoftext|>",
            "<|endoftext|>": "<|endoftext|>",
            "<|pad|>": "<|pad|>",
        }
        self.pat = re.compile(
            r"""<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[\p{L}]+|[\p{N}]|[^\s\p{L}\p{N}]+""",
            re.IGNORECASE,
        )

    def bpe(self, token: str) -> str:
        if token in self.cache:
            return self.cache[token]
        word = tuple(token[:-1]) + (token[-1] + "</w>",)
        pairs = get_pairs(word)
        if not pairs:
            return token + "</w>"
        while True:
            bigram = min(pairs, key=lambda pair: self.bpe_ranks.get(pair, float("inf")))
            if bigram not in self.bpe_ranks:
                break
            first, second = bigram
            new_word = []
            i = 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                except ValueError:
                    new_word.extend(word[i:])
                    break
                new_word.extend(word[i:j])
                i = j
                if word[i] == first and i < len(word) - 1 and word[i + 1] == second:
                    new_word.append(first + second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)
            if len(word) == 1:
                break
            pairs = get_pairs(word)
        out = " ".join(word)
        self.cache[token] = out
        return out

    def encode(self, text: str) -> list[int]:
        bpe_tokens = []
        text = re.sub(r"\s+", " ", text).strip()
        for token in re.findall(self.pat, text):
            token = "".join(self.byte_encoder[b] for b in token.encode("utf-8"))
            bpe_tokens.extend(self.encoder[bpe] for bpe in self.bpe(token).split(" "))
        return bpe_tokens

    def __call__(self, texts, context_length: int = CONTEXT_LENGTH) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        sot = self.encoder["<|startoftext|>"]
        eot = self.encoder["<|endoftext|>"]
        all_tokens = [[sot] + self.encode(text) + [eot] for text in texts]
        result = np.zeros((len(all_tokens), context_length), dtype=np.int64)
        for i, tokens in enumerate(all_tokens):
            if len(tokens) > context_length:
                tokens = tokens[:context_length]
                tokens[-1] = eot
            result[i, : len(tokens)] = tokens
        return result

    @staticmethod
    def default(model_dir) -> SimpleTokenizer:
        model_dir = Path(model_dir)
        return SimpleTokenizer(model_dir / "vocab.json", model_dir / "merges.txt")
