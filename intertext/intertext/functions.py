# -*- coding: utf-8 -*-


import collections
import itertools
import types
from intertext.constants import *


def set_match_hierarchy(hierarchy):
    if not isinstance(hierarchy, list) and not all(isinstance(i, int) for i in hierarchy):
        raise ValueError
    MATCH_HIERARCHY = hierarchy


def reset_match_hierarchy():
    MATCH_HIERARCHY = [1, 2, 3, 4, 5]


def co_occurrences(edgelist, focus="target"):
    if not isinstance(edgelist, (list, types.GeneratorType)):
        raise ValueError("edgelist must be list or generator and can only contain 2-tuples")
    nbrs = collections.defaultdict(set)
    co_occurrences = collections.defaultdict(set)
    for e in edgelist:
        if not (isinstance(e, tuple) and len(e) == 2):
            raise ValueError("edgelist must be list or generator and can only contain 2-tuples")
        k, v = e[0], e[1]
        if focus == "source":
            k, v = v, k
        nbrs[k].add(v)
    for k, v in nbrs.iteritems():
        for pair in itertools.combinations(v, 2):
            co_occurrences[pair].add(k)
    return co_occurrences


# L = [('a','b'),('a','c'),('b','c'),('b','d'),('b','p'),('a','d')]
# gen = (i for i in L)
