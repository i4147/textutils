from collections.abc import Sequence


def _levenshtein(a: Sequence[str], b: Sequence[str]) -> int:
    if len(b) > len(a):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def levenshtein_distance(a: str, b: str) -> int:
    return _levenshtein(a, b)


def levenshtein_similarity(a: str, b: str) -> float:
    length = max(len(a), len(b))
    return 1.0 if not length else 1.0 - levenshtein_distance(a, b) / length


def lcs_distance(a: str, b: str) -> int:
    if len(b) > len(a):
        a, b = b, a
    previous = [0] * (len(b) + 1)
    for x in a:
        current = [0]
        for j, y in enumerate(b, 1):
            current.append(previous[j - 1] + 1 if x == y else max(previous[j], current[-1]))
        previous = current
    return len(a) + len(b) - 2 * previous[-1]


def lcs_similarity(a: str, b: str) -> float:
    length = len(a) + len(b)
    return 1.0 if not length else 1.0 - lcs_distance(a, b) / length
