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

import re

EMAIL_FORMAT = re.compile(
    r"([a-zA-Z0-9!#$%&'\*\+\-/=?^_`{|}~,][a-zA-Z0-9!#$%&'\*\+\-\./=?^_`{|}~,]{1,63}@[\w\.-]{1,253}\.[\w\.-]{1,63})"
)
EMAIL_DOMAIN_FORMAT = re.compile(r"@([\w\.-]{1,253}\.[\w\.-]{1,63})")
PHONENUM_FORMAT = re.compile(r"(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$")


def extract_email_addresses(text):
    return re.findall(EMAIL_FORMAT, text)


def extract_email_domains(text):
    return re.findall(EMAIL_DOMAIN_FORMAT, text)


def extract_phone_number(text):
    return re.findall(PHONENUM_FORMAT, text)


def split_upc(Code):
    Code = re.sub("[^0-9]+", "", Code)
    SystemDigit = Code[0]
    CheckDigit = Code[-1]
    LLLLL = Code[1:6]
    RRRRR = Code[-6:-1]
    R1 = Code[-6]
    RRR_ = Code[-6:-3]
    _RR = Code[-3:-1]
    LR10 = Code[1:-1]

    return {
        "SystemDigit": SystemDigit,
        "CheckDigit": CheckDigit,
        "LLLLL": LLLLL,
        "RRRRR": RRRRR,
        "R1": R1,
        "RRR_": RRR_,
        "LR10": LR10,
    }


def upc_check_digit(Code):
    Code = re.sub("[^0-9]+", "", Code)

    DigitCount = len(Code)

    if DigitCount == 12:
        CheckFormula = np.array([3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1])
        Digits = np.zeros(DigitCount, dtype=np.int)
        for i in range(DigitCount - 1):
            Digits[i] = int(Code[i])
        M = np.sum(Digits * CheckFormula) % 10
        if M != 0:
            CheckDigitValue = 10 - M
        else:
            CheckDigitValue = 0
    else:
        CheckDigitValue = -1

    return CheckDigitValue


def check_upc(Code):
    CheckDigitValue = upc_check_digit(Code)
    if CheckDigitValue == int(Code[-1]):
        return True
    else:
        return False
