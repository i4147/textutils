from .backend import Backend
from .language import Language
from .readability import ReadabilityFormula
from .smoothtext import SmoothText

from importlib.metadata import version

__version__ = tuple(map(int, version("smoothtext").split(".")))

for module in (Backend, Language, ReadabilityFormula, SmoothText):
    for attr in dir(module):
        if callable(getattr(module, attr)):
            if not attr.startswith("_"):
                globals()[attr] = getattr(module, attr)
