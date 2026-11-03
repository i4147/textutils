from __future__ import annotations
import re
from typing import Iterable, Iterator, List, Tuple


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def tokenize_sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if n <= 0:
        raise ValueError("n must be >= 1")
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def contains(text: str, query: str) -> bool:
    return query.lower() in text.lower()


def find_all(text: str, query: str) -> list[int]:
    pattern = re.escape(query)
    return [m.start() for m in re.finditer(pattern, text, flags=re.I)]


def simple_stem(word: str) -> str:
    suffixes = ["ing", "ed", "ly", "es", "s"]
    for s in suffixes:
        if word.endswith(s) and len(word) > len(s) + 2:
            return word[: -len(s)]
    return word


def stream_read(path: str, chunk_size: int = 4096) -> Iterator[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except FileNotFoundError:
        raise
