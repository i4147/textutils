import re

from .strings import (
    INIWORD as INIWORD_STR,
    INILOW as INILOW_STR,
    CAMEL as CAMEL_STR,
    LITERAL as LITERAL_STR,
    WORD as WORD_STR,
    CAPWORD as CAPWORD_STR,
    DASH_CAPREST as DASH_CAPREST_STR,
    CAPREST as CAPREST_STR,
)

INIWORD = re.compile(INIWORD_STR)
INILOW = re.compile(INILOW_STR)
CAMEL = re.compile(CAMEL_STR)
LITERAL = re.compile(LITERAL_STR)
WORD = re.compile(WORD_STR)
CAPWORD = re.compile(CAPWORD_STR)
DASH_CAPREST = re.compile(DASH_CAPREST_STR)
CAPREST = re.compile(CAPREST_STR)
