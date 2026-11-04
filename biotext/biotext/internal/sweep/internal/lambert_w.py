import numpy as np


def lambert_w(branch, x, dtype=np.float64):
    x = np.asarray(x, dtype=np.float64)

    if branch == -1:
        w = -2 * np.ones_like(x)
    else:
        w = np.ones_like(x)

    v = np.inf * w

    with np.errstate(divide="ignore", invalid="ignore"):
        while np.any(np.abs(w - v) / np.abs(w) > 1e-8):
            v = w
            e = np.exp(w)
            f = w * e - x
            w = w - f / (e * (w + 1) - (w + 2) * f / (2 * w + 2))

    return w
