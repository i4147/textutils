# -*- coding: utf-8 -*-

__docformat__ = "restructuredtext"
__name__ = "TextLab"
__distname__ = "TextLab"
__version__ = "0.1.5"
__description__ = "A Text Analytics Toolkit (TextAnalyticsLab/TextLab) for Python"
__author__ = "Sumudu Tennakoon"
__url__ = "https://github.com/sptennak/TextAnalytics"
__create_date__ = "Sun Jul 10 2018"
__last_update__ = "Sat Dec 21 2019"
__license__ = """
Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
"""
__doc__ = """
TextAnalyticsLab (TextLab) - a collection of text analytics tools for python.
===========================================================
'TextAnalyticsLab' (TextLab) is a Python package providing a set of text analytics tools 
for data mining and machine learning projects and end-to-end text analytics 
application development. It is compatible with and interoperate with data 
analysis and manipulation library Pandas,  natural language processing library 
nltk, Machine Lerning TookKit (pymltoolkit|mltk), and many other AI and machine 
learning platforms.

Main Features
-------------
- Text Similarity
- OCR (A wrapper to convert image documents to text using Tesseract-OCR and Ghostscript)
- Text Mining and Information Extraction (in v0.2.0)
- Cleaning Text content
- Web Scraping (in v0.1.6)
- Email Data Extraction
- Classification of Text Conent (in v0.2.0)

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

hard_dependencies = ("numpy", "scipy", "matplotlib", "pandas", "mltk", "bs4", "PIL")
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append(dependency)

if missing_dependencies:
    raise ImportError(
        "Following packages are required but missing in the Python distribution: {}".format(missing_dependencies)
    )
del hard_dependencies, dependency, missing_dependencies

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

from textlab.similarity import *
from textlab.mining import *
from textlab.process import *
from textlab.scrape import *
from textlab.classification import *
from textlab.ocr import *
from textlab.email import *

print("textlab=={}".format(__version__.strip()))
pd.set_option("display.max_columns", 1000)
pd.set_option("display.max_rows", 500)
pd.set_option("expand_frame_repr", False)
pd.set_option("large_repr", "truncate")
pd.set_option("precision", 5)
