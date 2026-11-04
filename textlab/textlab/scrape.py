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
import io
import requests
from timeit import default_timer as timer
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import warnings
import bs4

warnings.filterwarnings("ignore")
from itertools import product, combinations, permutations, combinations_with_replacement


def pandas_read_string(string, sep=",", header="infer", names=None, nrows=None, lineterminator=None, comment=None):
    try:
        return pd.read_csv(
            io.StringIO(string),
            sep=sep,
            header=header,
            names=names,
            nrows=nrows,
            lineterminator=lineterminator,
            comment=comment,
        )
    except:
        print("Error Converting String to DataFrame: {}".format(traceback.print_exc()))
    return pd.DataFrame()


def find_pattern_webpage(targetPage, pattern):
    source = requests.get(targetPage).text
    soup = bs4.BeautifulSoup(source, "lxml")
    text = soup.getText()
    try:
        result = re.search(pattern, text)
    except:
        result = None
    return result


def extract_tables_webpage(target_page):
    source = requests.get(target_page).text
    soup = bs4.BeautifulSoup(source, "lxml")
    tableStr = soup.decode()
    data_frames = pd.read_html(tableStr)
    return data_frames


def html_to_text(source, tags_to_ignore=["script", "style"]):

    soup = bs4.BeautifulSoup(source)
    for script in soup(tags_to_ignore):
        script.decompose()

    text = soup.get_text()

    return text
