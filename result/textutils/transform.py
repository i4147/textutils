"""Small text transformations and sentence tokenization."""

import random
import re


def leetspeak(text: str) -> str:
    """Uppercase text and replace A, E, I and O with digits (textfun)."""
    return text.upper().translate(str.maketrans({"A": "4", "E": "3", "I": "1", "O": "0"}))


class SpongeString:
    """Randomize character case using a percentage per whitespace-delimited word.

    Unlike the original spongetext implementation, whitespace is preserved.
    Pass an explicit random generator for reproducible results.
    """

    def __init__(self, string: str, spongeness: int = 6, *, rng: random.Random | None = None) -> None:
        if not 1 <= spongeness <= 10:
            raise ValueError("spongeness must be between 1 and 10")
        self.original = string
        self.spongeness = spongeness
        generator = rng if rng is not None else random.Random()

        def transform(match: re.Match[str]) -> str:
            word = match.group()
            positions = set(generator.sample(range(len(word)), len(word) * spongeness // 10))
            return "".join(char.upper() if i in positions else char.lower() for i, char in enumerate(word))

        self.text = re.sub(r"\S+", transform, string)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"SpongeString({self.original!r}, spongeness={self.spongeness})"


class SimpleSentenceTokenizer:
    """Split after terminal punctuation followed by whitespace, retaining a final fragment.

    This is a simple heuristic, not a language-aware sentence segmenter.
    """

    def __init__(self, breaking_chars: str = ".!?") -> None:
        if not breaking_chars:
            raise ValueError("breaking_chars must not be empty")
        self._split = re.compile(rf"(?<=[{re.escape(breaking_chars)}])\s+")

    def __call__(self, text: str) -> list[str]:
        """Return nonempty, stripped sentence fragments."""
        return [part for part in self._split.split(text.strip()) if part]
