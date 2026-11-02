import sys
from typing import TYPE_CHECKING, Optional, Union
from colorama import just_fix_windows_console
from .abc import as_path
from .texttree import PyDir, PyFile

if TYPE_CHECKING:
    from pathlib import Path
    from .abc import TextTree
__all__ = ["DEFAULT_IGNORED_PATHS", "file", "fromstr", "module"]
DEFAULT_IGNORED_PATHS = ["build", "dist", ".git", ".github"]
just_fix_windows_console()


def module(
    path_or_str: Path | str,
    /,
    home: Optional[Path | str] = None,
    encoding: Optional[str] = None,
    ignore: Optional[list[str]] = None,
    include: Optional[list[str]] = None,
) -> "TextTree":
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if not (path := as_path(path_or_str, home=home)).exists():
        msg = f"file not found: '{path}'"
        raise FileNotFoundError(msg)
    if path.is_file():
        return PyFile(path, home=home, encoding=encoding)
    if ignore is None:
        ignore = sys.modules[__name__.rpartition(".")[0]].DEFAULT_IGNORED_PATHS
    return PyDir(path, home=home, encoding=encoding, ignore=ignore, include=include)


def file(
    path_or_str: Path | str,
    /,
    home: Optional[Path | str] = None,
    encoding: Optional[str] = None,
) -> "TextTree":
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if not (path := as_path(path_or_str, home=home)).exists():
        msg = f"file not found: '{path}'"
        raise FileNotFoundError(msg)
    if path.is_file():
        return PyFile(path, home=home, encoding=encoding)
    msg = f"is a directory: '{path}'"
    raise IsADirectoryError(msg)


def fromstr(string: Path | str, /) -> "TextTree":
    return PyFile(string)
