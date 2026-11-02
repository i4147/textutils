import functools
import math
import sys
import numpy as np
import scipy

MAX_SWAP_LEVEL = 4 - 2 * math.sqrt(3) - sys.float_info.epsilon
SWAP_START_STATE = np.array([0, 0, 0, 0, 0, 0, 0, 1])
SWAP_LEVENSHTEIN_VALUE = np.array([1, 0, 0, 2, 0, 2, 0, 0])


def __compute_expected_cer_from_noise_level(p: float, N: int) -> float:
    p = float(p)
    q = 1 - p
    P = np.array([
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, p, q, 0, 0, 0],
        [p, q, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, p, q, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, p, q, 0, 0, 0],
        [0, 0, 0, 0, 0, p, q, 0],
    ])
    state = SWAP_START_STATE
    levenshtein = state @ SWAP_LEVENSHTEIN_VALUE
    for _ in range(N - 1):
        state = state @ P
        levenshtein += state @ SWAP_LEVENSHTEIN_VALUE
    return levenshtein / N


@functools.cache
def __compute_noise_level_from_expected_cer(cer: float, N: int) -> float:
    return float(
        scipy.optimize.fsolve(
            lambda x: __compute_expected_cer_from_noise_level(float(x[0]), N) - cer,
            [0],
        )[0]
    )


@functools.lru_cache
def unbias_swap(p: float, N: int) -> float:
    p = min(p, MAX_SWAP_LEVEL)
    if N == 0:
        return p
    if p == 0:
        return 0
    if N > 50:
        return (2 - p) / 2 - math.sqrt((p**2) - (8 * p) + 4) / 2
    return __compute_noise_level_from_expected_cer(p, N)


def unbias_split_into_words(p: float, text: list[str]) -> float:
    n_chars = sum(map(len, text))
    n_spaces = len(text) - 1
    return p * (1 + n_spaces / n_chars)


def unbias_several_action(p: float, n_actions: int) -> float:
    p_effective: float = 1.0 - (1.0 - p) ** (1 / n_actions)
    return p_effective
