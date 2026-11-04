import numpy as np
from .lambert_w import lambert_w


def transform_with_lambert_w(kmer_counts):
    fx = lambda x: (-lambert_w(0, -np.exp(-x) * x)) ** 0.1

    u = fx(kmer_counts)

    u[u == 0] = -1

    return u
