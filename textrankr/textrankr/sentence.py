from typing import Tuple

from collections import Counter


__all__: Tuple[str, ...] = ("Sentence",)


class Sentence:
    def __init__(self, index: int, text: str, bow: Counter) -> None:
        self.index: int = index
        self.text: str = text
        self.bow: Counter = bow

    def __str__(self) -> str:
        return self.text

    def __hash__(self) -> int:
        return self.index
