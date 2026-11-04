from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Protocol, Sequence

import numpy as np


class TextRule(Protocol):
    def apply(self, text: str, rng: np.random.Generator) -> str: ...


@dataclass
class Substitute:
    mapping: Mapping[str, str]
    probability: float = 1.0

    def apply(self, text: str, rng: np.random.Generator) -> str:
        if not self.mapping:
            return text
        pattern = re.compile("|".join(re.escape(k) for k in sorted(self.mapping, key=len, reverse=True)))

        def replace(match: re.Match[str]) -> str:
            if self.probability >= 1.0 or rng.random() < self.probability:
                return self.mapping[match.group(0)]
            return match.group(0)

        return pattern.sub(replace, text)


@dataclass
class Drop:
    chars: str
    probability: float = 0.2
    keep_first: bool = True
    """Keep a letter at the start of a word. It usually carries the vowel."""

    def apply(self, text: str, rng: np.random.Generator) -> str:
        out = []
        at_word_start = True
        for ch in text:
            drop = ch in self.chars and not (self.keep_first and at_word_start) and rng.random() < self.probability
            if not drop:
                out.append(ch)
            at_word_start = ch.isspace() or _is_punctuation(ch)
        return "".join(out)


@dataclass
class Swap:
    pairs: Sequence[tuple[str, str]]
    probability: float = 0.3

    def apply(self, text: str, rng: np.random.Generator) -> str:
        alternatives: dict[str, list[str]] = {}
        for a, b in self.pairs:
            alternatives.setdefault(a, []).append(b)
            alternatives.setdefault(b, []).append(a)
        out = []
        for ch in text:
            options = alternatives.get(ch)
            if options and rng.random() < self.probability:
                out.append(options[int(rng.integers(len(options)))])
            else:
                out.append(ch)
        return "".join(out)


@dataclass
class Regex:
    pattern: str
    replacement: str
    probability: float = 1.0

    def apply(self, text: str, rng: np.random.Generator) -> str:
        compiled = re.compile(self.pattern)

        def replace(match: re.Match[str]) -> str:
            if self.probability >= 1.0 or rng.random() < self.probability:
                return match.expand(self.replacement)
            return match.group(0)

        return compiled.sub(replace, text)


@dataclass
class Callback:
    function: "Callable[[str], str]"

    def apply(self, text: str, rng: np.random.Generator) -> str:
        return self.function(text)


@dataclass
class RuleSet:
    rules: Sequence[TextRule] = field(default_factory=tuple)

    def apply(self, text: str, rng: np.random.Generator) -> str:
        for rule in self.rules:
            text = rule.apply(text, rng)
        return text


EQUIVALENT_LETTERS: tuple[tuple[str, str], ...] = (
    ("ك", "ک"),
    ("ي", "ی"),
    ("ي", "ى"),
    ("ة", "ه"),
    ("ه", "ھ"),
    ("ف", "ڤ"),
    ("ک", "ݢ"),
    ("ز", "ژ"),
    ("و", "ۏ"),
)

HAMZA_FORMS: Mapping[str, str] = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ؤ": "و",
    "ئ": "ي",
}

OPTIONAL_LETTERS = "اوي"

DIACRITICS = "".join(chr(c) for c in range(0x064B, 0x0653)) + "ٰـ"


def orthographic_variation(
    *,
    swap: float = 0.25,
    drop_letters: float = 0.0,
    drop_hamza: float = 0.2,
    strip_diacritics: float = 1.0,
    pairs: Iterable[tuple[str, str]] = EQUIVALENT_LETTERS,
    optional_letters: str = OPTIONAL_LETTERS,
) -> RuleSet:
    rules: list[TextRule] = []
    if strip_diacritics > 0:
        rules.append(Drop(DIACRITICS, probability=strip_diacritics, keep_first=False))
    if drop_hamza > 0:
        rules.append(Substitute(HAMZA_FORMS, probability=drop_hamza))
    if swap > 0:
        rules.append(Swap(tuple(pairs), probability=swap))
    if drop_letters > 0:
        rules.append(Drop(optional_letters, probability=drop_letters))
    return RuleSet(rules)


def _is_punctuation(ch: str) -> bool:
    import unicodedata

    return unicodedata.category(ch).startswith("P")
