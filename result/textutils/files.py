"""UTF-8 text file reading and parallel directory search."""

from collections.abc import Iterator
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

from loguru import logger


@dataclass(frozen=True)
class TextFile:
    """Read and search a UTF-8 text file; line numbers start at one."""

    path: Path

    def read(self) -> str:
        """Read the file as UTF-8, propagating I/O and decoding errors."""
        return self.path.read_text(encoding="utf-8")

    def search(self, needle: str) -> list[tuple[int, str]]:
        """Return line numbers and matching lines without line terminators."""
        return [(i, line) for i, line in enumerate(self.read().splitlines(), 1) if needle in line]


def iter_text_files(root: Path, pattern: str = "*.txt") -> Iterator[Path]:
    """Yield matching regular files recursively, in deterministic path order.

    Symbolic links to files are included; directory symlinks are not followed.
    """
    if not root.is_dir():
        raise NotADirectoryError(root)
    yield from sorted(path for path in root.rglob(pattern) if path.is_file())


def _search_one(task: tuple[Path, str]) -> tuple[Path, list[tuple[int, str]]]:
    path, needle = task
    return path, TextFile(path).search(needle)


def search_files(root: Path, needle: str, pattern: str = "*.txt") -> Iterator[tuple[Path, list[tuple[int, str]]]]:
    """Search matching files using four processes, yielding results in completion order.

    Empty matches are omitted. Worker I/O and UTF-8 decoding errors propagate to
    the caller. Close the iterator when stopping early to release worker processes.
    """
    logger.debug("Searching {} for {!r}", root, needle)
    tasks = ((path, needle) for path in iter_text_files(root, pattern))
    with Pool(processes=4) as pool:
        for path, matches in pool.imap_unordered(_search_one, tasks):
            if matches:
                yield path, matches
