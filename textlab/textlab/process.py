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


def normalize_text(text, method="str"):

    text = text.lower()

    if method == "str":
        text = "".join(c for c in text if not c.isdigit())
        from string import punctuation

        text = "".join(c for c in text if c not in punctuation)
        text = " ".join(text.split())

    elif method == "regex":
        import re

        text = re.sub(r"\d+", " ", text)
        text = re.sub(r"\W+", " ", text)
        text = re.sub("\s\s+", " ", text)

    return text


def remove_quoted_printable_encoding(Text):
    QPCTE = {
        "= ": " ",
        "==09": "",
        "==20": " ",
        "=\t": "\t",
        "=\n": "",
        "=09": "\t",
        "=0A": "\n",
        "=0C": "\f",
        "=0D": "\r",
        "=0D=0A": "\r\n",
        "=20": " ",
        "=21": "!",
        "=22": '"',
        "=23": "#",
        "=24": "$",
        "=25": "%",
        "=26": "&",
        "=27": "'",
        "=28": "(",
        "=29": ")",
        "=2A": "*",
        "=2B": "+",
        "=2C": ",",
        "=2D": "-",
        "=2E": ".",
        "=2F": "/",
        "=3A": ":",
        "=3B": ";",
        "=3C": "<",
        "=3D": "=",
        "=3E": ">",
        "=3F": "?",
        "=85": "...",
        "=91": "'",
        "=92": "'",
        "=93": '"',
        "=94": '"',
        "=95": "\x95",
        "=96": "-",
        "=97": "--",
        "=98": "~",
        "=99": "\x99",
        "=A9": "\xa9",
        "=AE": "\xae",
        "=E0": "\xe0",
        "=E1": "\xe1",
        "=E2": "\xe2",
        "=E3": "\xe3",
        "=E4": "\xe4",
        "=E8": "\xe8",
        "=E9": "\xe9",
        "=EA": "\xea",
        "=EB": "\xeb",
        "=EC": "\xec",
        "=ED": "\xed",
        "=EE": "\xee",
        "=F1": "\xf1",
        "=F2": "\xf2",
        "=F3": "\xf3",
        "=F4": "\xf4",
        "=F5": "\xf5",
        "=F6": "\xf6",
        "=F7": "\xf7",
        "=F8": "\xf8",
        "=F9": "\xf9",
        "=FA": "\xfa",
        "=FB": "\xfb",
        "=FC": "\xfc",
        "=FD": "\xfd",
    }

    for pattern, replacement in QPCTE.items():
        Text = Text.replace(pattern, replacement)

    return Text


def remove_html_tags(Text):
    rules = [
        {r"[\x20][\x20]+": " "},
        {r"\s*<br\s*/?>\s*": "\n"},
        {r"</(p|h\d)\s*>\s*": "\n\n"},
        {r"<head>.*<\s*(/head|body)[^>]*>": ""},
        {r"<script>.*<\s*/script[^>]*>": ""},
        {r"<style>.*<\s*/style[^>]*>": ""},
        {r"<[^<]*?/?>": ""},
    ]

    for rule in rules:
        for pattern, replacement in rule.items():
            Text = re.sub(pattern, replacement, Text)

    return Text


def parse_html_entities(text):
    enities = {
        "cent;": "\xa2",
        "&pound;": "\xa3",
        "&copy;": "\xa9",
        "&reg;": "\xae",
        "&plusmn;": "\xb1",
        "&frac14;": "\xbc",
        "&frac12;": "\xbd",
        "&frac34;": "\xbe",
        "&times;": "\xd7",
        "&prime;": "\x2032",
        "&Prime": "\x2033",
        "&lowast;": "\x2217",
        "&ne;": "\x2260",
        "&trade;": "\x2122",
        "&#8211;": "\x8211",
        "&#8217;": "\x8217",
        "&amp;": "&",
    }

    for pattern, replacement in enities.items():
        text = text.replace(pattern, replacement)

    return text


def remove_consecutive_whitespace(text, axis=None):

    if axis == 0 or axis == None:
        text = re.sub("[\n][\n]+", "\n", text)
        text = re.sub("[\r][\r]+", "\r", text)

    if axis == 1 or axis == None:
        text = re.sub("[\x20][\x20]+", " ", text)
        text = re.sub("[\t][\t]+", "\t", text)

    text = text.strip()

    return text
