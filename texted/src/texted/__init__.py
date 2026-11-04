from ._edit import Edition, add_prefix, edit, remove_prefix, replace
from ._predicate import (
    Predicate,
    blank,
    contains,
    endswith,
    fullmatch,
    glob,
    match,
    negate,
    pred,
    search,
    startswith,
)
from ._single_selection import Selection, everything, find, until, whilist

try:
    from ._version import __version__
except ImportError:
    __version__ = "undefined"

__all__ = [
    "__version__",
    "Predicate",
    "blank",
    "contains",
    "endswith",
    "fullmatch",
    "glob",
    "match",
    "negate",
    "pred",
    "search",
    "startswith",
    "Selection",
    "everything",
    "find",
    "until",
    "whilist",
    "Edition",
    "add_prefix",
    "edit",
    "remove_prefix",
    "replace",
]
