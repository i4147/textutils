import numpy as np
from numpy.linalg import norm
from collections import namedtuple

Segmentation = namedtuple("Segmentation", "total splits gains min_gain optimal")


def split_greedy(docmat, penalty=None, max_splits=None):
    L, dim = docmat.shape
    assert max_splits is not None or (penalty is not None and penalty > 0)
    cumvecs = np.cumsum(np.vstack((np.zeros((1, dim)), docmat)), axis=0)
    cuts = [0, L]
    segscore = dict()
    segscore[0] = norm(cumvecs[L, :] - cumvecs[0, :], ord=2)
    segscore[L] = 0
    score_l = norm(cumvecs[:L, :] - cumvecs[0, :], axis=1, ord=2)
    score_r = norm(cumvecs[L, :] - cumvecs[:L, :], axis=1, ord=2)
    score_out = np.zeros(L)
    score_out[0] = -np.inf
    score = score_out + score_l + score_r
    min_gain = np.inf
    while True:
        split = np.argmax(score)
        if score[split] == -np.inf:
            break
        cut_l = max([c for c in cuts if c < split])
        cut_r = min([c for c in cuts if split < c])
        split_gain = score_l[split] + score_r[split] - segscore[cut_l]
        if penalty is not None:
            if split_gain < penalty:
                break
        min_gain = min(min_gain, split_gain)
        segscore[cut_l] = score_l[split]
        segscore[split] = score_r[split]
        cuts.append(split)
        cuts = sorted(cuts)
        if max_splits is not None:
            if len(cuts) >= max_splits + 2:
                break
        score_l[split:cut_r] = norm(cumvecs[split:cut_r, :] - cumvecs[split, :], axis=1, ord=2)
        score_r[cut_l:split] = norm(cumvecs[split, :] - cumvecs[cut_l:split, :], axis=1, ord=2)
        score_out += split_gain
        score_out[cut_l:split] += segscore[split] - split_gain
        score_out[split:cut_r] += segscore[cut_l] - split_gain
        score_out[split] = -np.inf
        score = score_out + score_l + score_r
    cuts = sorted(cuts)
    splits = cuts[1:-1]
    if penalty is None:
        total = None
    else:
        total = (
            sum(norm(cumvecs[l, :] - cumvecs[r, :], ord=2) for l, r in zip(cuts[:-1], cuts[1:])) - len(splits) * penalty
        )
    gains = []
    for beg, cen, end in zip(cuts[:-2], cuts[1:-1], cuts[2:]):
        no_split_score = norm(cumvecs[end, :] - cumvecs[beg, :], ord=2)
        gains.append(segscore[beg] + segscore[cen] - no_split_score)
    return Segmentation(total, splits, gains, min_gain=min_gain, optimal=None)


def split_optimal(docmat, penalty, seg_limit=None):
    L, dim = docmat.shape
    lim = L if seg_limit is None else seg_limit
    assert lim > 0
    assert penalty > 0
    acc = np.full((L, lim), -np.inf, dtype=np.float32)
    colmax = np.full((L,), -np.inf, dtype=np.float32)
    ptr = np.zeros(L, dtype=np.int32)
    for i in range(L):
        score_so_far = colmax[i - 1] if i > 0 else 0.0
        ctxvecs = np.cumsum(docmat[i : i + lim, :], axis=0)
        winsz = ctxvecs.shape[0]
        score = norm(ctxvecs, axis=1, ord=2)
        acc[i, :winsz] = score_so_far - penalty + score
        deltas = np.where(acc[i, :winsz] > colmax[i : i + lim])[0]
        js = i + deltas
        colmax[js] = acc[i, deltas]
        ptr[js] = i
    path = [ptr[-1]]
    while path[0] != 0:
        path.insert(0, ptr[path[0] - 1])
    splits = path[1:]
    gains = get_gains(docmat, path[1:])
    optimal = all(np.diff([0] + splits + [L]) < lim)
    total = colmax[-1] + penalty
    return Segmentation(total, splits, gains, min_gain=None, optimal=optimal)


def get_total(docmat, splits, penalty):
    L, dim = docmat.shape
    cuts = [0] + list(splits) + [L]
    cumvecs = np.cumsum(np.vstack((np.zeros((1, dim)), docmat)), axis=0)
    return sum(norm(cumvecs[l, :] - cumvecs[r, :], ord=2) for l, r in zip(cuts[:-1], cuts[1:])) - len(splits) * penalty


def get_gains(docmat, splits, width=None):
    gains = []
    L = docmat.shape[0]
    for beg, cen, end in zip([0] + splits[:-1], splits, splits[1:] + [L]):
        if width is not None and width > 0:
            beg, end = max(cen - width, 0), min(cen + width, L)
        slice_l, slice_r, slice_t = [slice(beg, cen), slice(cen, end), slice(beg, end)]
        gains.append(
            norm(docmat[slice_l, :].sum(axis=0), ord=2)
            + norm(docmat[slice_r, :].sum(axis=0), ord=2)
            - norm(docmat[slice_t, :].sum(axis=0), ord=2)
        )
    return gains
