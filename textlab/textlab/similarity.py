# -*- coding: utf-8 -*-
# TextAnalytics (textanalytics)
__name__ = "mltk"
"""
TextAnalytics - a collection of text analytics tools for python.
===========================================================
'TextAnalytics' is a Python package providing a set of text analytics tools 
for data mining and machine learning projects and end-to-end text analytics 
application development. 

Author
------
- Sumudu Tennakoon

Links
-----
Website: http://sumudu.tennakoon.net/projects/TextAnalytics
Github: https://github.com/sptennak/TextAnalytics

License
-------
Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
"""

from datetime import datetime
import gc
import traceback
import gc
import os
from timeit import default_timer as timer
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import warnings

warnings.filterwarnings("ignore")
from itertools import product, combinations, permutations, combinations_with_replacement


def damerau_levenshtein_distance(str1, str2, case_sensitive=True, normalized=False):
    if not case_sensitive:
        str1 = str1.lower()
        str2 = str2.lower()

    if str1 == str2:
        return 0
    elif len(str1) == 0:
        return len(str2)
    elif len(str2) == 0:
        return len(str1)

    len_str1 = len(str1)
    len_str2 = len(str2)
    len_cost = 0

    d = np.zeros((len_str1 + 1, len_str2 + 1), dtype=np.int)

    for i in range(len_str1 + 1):
        d[i][0] = i

    for j in range(len_str2 + 1):
        d[0][j] = j

    # print(d)

    for i in range(1, len_str1 + 1):
        for j in range(1, len_str2 + 1):
            # print(i, j)
            if str1[i - 1] == str2[j - 1]:
                len_cost = 0
            else:
                len_cost = 1

            d[i][j] = min(
                d[i - 1][j] + 1,
                d[i][j - 1] + 1,
                d[i - 1][j - 1] + len_cost,
            )

            if (i > 1) and (j > 1) and (str1[i - 1] == str2[j - 2]) and (str1[i - 2] == str2[j - 1]):
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + len_cost)
    # print(d)
    dld = d[len_str1][len_str2]
    if normalized:
        try:
            n_dld = float(dld) / max(len_str1, len_str2)
        except:
            print("Error:\n{}".format(traceback.format_exc()))
            n_dld = None
        return n_dld
    else:
        return dld


def get_substrings(string, case_sensitive=True, min_length=1, max_length=np.inf):
    # from itertools import combinations
    if not case_sensitive:
        string = string.lower()
    len_string = len(string)
    # substring_set = set(string[i:j+1] for i in range(len_string) for j in range(i,len_string))
    substring_set = set(
        string[x:y] if ((y - x) >= min_length and (y - x) <= max_length) else None
        for x, y in combinations(range(len_string + 1), r=2)
    ) - {None}
    # print(substring_set)
    return list(substring_set)


def jaccard_index(str1, str2, method="words", case_sensitive=True, min_length=1, max_length=np.inf):

    # from itertools import combinations
    if not case_sensitive:
        str1 = str1.lower()
        str2 = str2.lower()

    if str1 == str2:
        return 1

    if method == "words":
        set1 = set(str1.split())
        set2 = set(str2.split())
    elif method == "substring":
        len_str1 = len(str1)
        len_str2 = len(str2)
        # set1 = set(str1[i:j+1] for i in range(len_str1) for j in range(i,len_str1))
        # set2 = set(str2[i:j+1] for i in range(len_str2) for j in range(i,len_str2))
        set1 = set(
            str1[x:y] if ((y - x) >= min_length and (y - x) <= max_length) else None
            for x, y in combinations(range(len_str1 + 1), r=2)
        ) - {None}
        set2 = set(
            str2[x:y] if ((y - x) >= min_length and (y - x) <= max_length) else None
            for x, y in combinations(range(len_str2 + 1), r=2)
        ) - {None}
        # print(set1)
        # print(set2)
    return float(len(set1 & set2)) / len(set1 | set2)
