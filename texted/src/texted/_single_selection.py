from __future__ import annotations

from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Callable, Iterator, TypeVar, cast

from ._predicate import Predicate, negate

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    _Select: TypeAlias = Callable[[list[str], slice | None], slice]
else:
    _Select = "_Select"


T = TypeVar("T", bound="Selection")


class Selection(ABC):
    @abstractmethod
    def _select(self, lines: list[str]) -> Iterator[slice]: ...

    @abstractmethod
    def __rshift__(self: T, op: _Select) -> T: ...

    def enumerate(self, lines: list[str]) -> Iterator[tuple[int, str]]:
        len_ = len(lines)
        for _slice in self._select(lines):
            _range = range(_slice.start or 0, _slice.stop or len_, _slice.step or 1)
            yield from zip(_range, lines[_slice])


class _SingleSelection(Selection):
    def __init__(self, op: _Select):
        self._op: _Select = op._op if isinstance(op, _SingleSelection) else op

    def _select(self, lines: list[str]) -> Iterator[slice]:
        yield self(lines, None)

    def __call__(self, lines: list[str], base: slice | None) -> slice:
        return self._op(lines, base)

    def __rshift__(self, op: _Select) -> _SingleSelection:
        other_op = op._op if isinstance(op, _SingleSelection) else op
        self_op = self._op

        def _chain(lines: list[str], base: slice | None) -> slice:
            return other_op(lines, self_op(lines, base))

        return _SingleSelection(_chain)


def _until(pred: Predicate, lines: list[str], base: slice | None) -> slice:
    len_lines = len(lines)
    base = base or slice(0)
    start = base.start or 0
    stop = base.stop or start
    step = base.step or 1

    selections = (slice(start, i, step) for i in range(stop, len_lines, step) if pred(lines[i]))
    return next(selections, slice(start, len_lines, step))


def until(pred: Predicate) -> _SingleSelection:
    return _SingleSelection(cast(_Select, partial(_until, pred)))


def whilist(pred: Predicate) -> _SingleSelection:
    return until(negate(pred))


def find(pred: Predicate) -> _Select:

    def _find(lines: list[str], base: slice | None) -> slice:
        return next(_find_all(pred, lines, base), slice(0))

    return _SingleSelection(_find)


def _find_all(pred: Predicate, lines: list[str], base: slice | None) -> Iterator[slice]:
    base = base or slice(0, len(lines))
    return (slice(i, i + 1) for i, line in enumerate(lines[base]) if pred(line))


def everything(lines: list[str], base: slice | None) -> slice:
    return base or slice(0, len(lines))
