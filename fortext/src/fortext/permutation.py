import itertools as it
from collections.abc import Generator


def permutations(
    string: str, max_len: int | None = None, min_len: int = 1, *, allow_repetition: bool = False
) -> Generator[str, None, None]:
    max_len = len(string) if max_len is None else max_len

    if min_len <= 0:
        min_len = 1

    if min_len > max_len:
        return

    if allow_repetition:
        for i in range(min_len, max_len + 1):
            for p in it.product(string, repeat=i):
                yield "".join(p)
    else:
        for i in range(min_len, max_len + 1):
            for p in it.permutations(string, i):
                yield "".join(p)
