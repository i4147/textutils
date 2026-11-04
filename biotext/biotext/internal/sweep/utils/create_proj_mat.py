import numpy as np
from .orthrand import orthrand


def create_proj_mat(rows, cols):
    Um = np.sin(range(1, cols + 1))
    Un = np.sin(range(1, rows + 1))
    xnorm = np.sqrt(rows / 3)
    idx = list(range(0, rows))
    R = (1 / xnorm) * orthrand(idx, Um, Un)
    return R
