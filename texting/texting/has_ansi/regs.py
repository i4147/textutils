import re
from warnings import simplefilter

from texting.has_ansi.elements import ANSI_ELEMENTS, ASTRAL_ELEMENTS, CHINESE_ELEMENTS

simplefilter(action="ignore", category=FutureWarning)

ANSI = re.compile("|".join(ANSI_ELEMENTS))
ASTRAL = re.compile("|".join(ASTRAL_ELEMENTS))
HAN = re.compile("|".join(CHINESE_ELEMENTS))
