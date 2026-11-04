import numpy as np


def orthrand(xlines, Um, Un):
    maxcol = len(Um)

    nlines = len(xlines)
    Un = Un[xlines]

    Z1 = np.float32(10**8 * (10**4 * Um - np.trunc(10**4 * Um)))
    Z2 = np.float32(10**8 * (10**4 * Un - np.trunc(10**4 * Un)))

    Z1 = np.repeat([Z1], nlines, axis=0)
    Z2 = np.repeat([Z2], maxcol, axis=0).T

    mret = np.sin(Z1 * Z2)

    return mret
