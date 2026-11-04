from functools import partial
from typing import TYPE_CHECKING, Callable, List, Union, cast, overload

from ._predicate import Predicate, blank
from ._single_selection import Selection, everything

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    Edition: TypeAlias = Callable[[List[str], slice], List[str]]
else:
    Edition = "Edition"


def replace(fn: Callable[[str], str]) -> Edition:
    return cast(Edition, partial(_replace, fn))


def _replace(fn: Callable[[str], str], lines: List[str], select: slice) -> List[str]:
    selected_lines = lines[select]
    if len(selected_lines) < 1:
        return lines

    replacement = _splitlines(fn("\n".join(selected_lines)))
    start = select.start or 0
    stop = select.stop or len(lines)
    return lines[:start] + replacement + lines[stop:]


def add_prefix(prefix: str, skip: Union[Predicate, None] = blank) -> Edition:
    pred = skip or (lambda _: False)
    return replace(lambda text: _indent(text, prefix, pred))


def remove_prefix(prefix, skip: Union[Predicate, None] = blank) -> Edition:
    pred = skip or (lambda _: False)
    return replace(lambda text: _dedent(text, prefix, pred))


def _dedent(text: str, prefix: str, skip: Predicate) -> str:
    i = len(prefix)
    return "\n".join(line[i:] if not skip(line) and line.startswith(prefix) else line for line in _splitlines(text))


def _indent(text: str, prefix: str, skip: Predicate) -> str:
    return "\n".join((prefix + line) if not skip(line) else line for line in _splitlines(text))


def _splitlines(text: str):
    return [""] if text == "" else text.splitlines()


@overload
def edit(text: str, edition: Edition) -> str: ...


@overload
def edit(text: str, select: Selection, edition: Edition) -> str: ...


def edit(text, select, edition=None):
    if edition is None:
        edition = select
        select = everything

    lines = text.splitlines()
    all_text = slice(len(lines))
    new_select = select(lines, all_text)
    return "\n".join(edition(lines, new_select))
