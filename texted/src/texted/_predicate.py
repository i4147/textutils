import fnmatch
import re
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    Predicate: TypeAlias = Callable[[str], bool]
else:
    Predicate = "Predicate"


class _Predicate:
    def __init__(self, pred: Predicate):
        self._pred: Predicate = pred._pred if isinstance(pred, _Predicate) else pred

    def __call__(self, line: str) -> bool:
        return self._pred(line)

    def __and__(self, other: Predicate) -> "_Predicate":
        self_pred = self._pred
        other_pred = other._pred if isinstance(other, _Predicate) else other
        return _Predicate(lambda line: self_pred(line) and other_pred(line))

    def __or__(self, other: Predicate) -> "_Predicate":
        self_pred = self._pred
        other_pred = other._pred if isinstance(other, _Predicate) else other
        return _Predicate(lambda line: self_pred(line) or other_pred(line))

    def __invert__(self) -> "_Predicate":
        self_pred = self._pred
        return _Predicate(lambda line: not self_pred(line))

    def __rrshift__(self, fn: Callable[[str], str]) -> "_Predicate":
        self_pred = self._pred
        return _Predicate(lambda line: self_pred(fn(line)))


def pred(fn: Callable[[str], Any]) -> _Predicate:
    return _Predicate(lambda line: bool(fn(line)))


def negate(fn: Predicate) -> _Predicate:
    return ~_Predicate(fn)


def startswith(prefix: str) -> _Predicate:
    return _Predicate(lambda line: line.startswith(prefix))


def endswith(suffix: str) -> _Predicate:
    return _Predicate(lambda line: line.endswith(suffix))


def contains(part: str) -> _Predicate:
    return _Predicate(lambda line: part in line)


def search(pattern: str, flags: int = 0) -> _Predicate:
    pat = re.compile(pattern, flags)
    return pred(pat.search)


def match(pattern: str, flags: int = 0) -> _Predicate:
    pat = re.compile(pattern, flags)
    return pred(pat.match)


def fullmatch(pattern: str, flags: int = 0) -> _Predicate:
    pat = re.compile(pattern, flags)
    return pred(pat.fullmatch)


def glob(pattern: str, flags: int = 0) -> _Predicate:
    return fullmatch(fnmatch.translate(pattern), flags)


blank = ~pred(str.strip)
"""Similar to ``str.strip >> negate(bool)``

>>> blank("hi")
False
>>> blank("    ")
False
"""
