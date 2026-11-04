from collections.abc import Iterator
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

from loguru import logger


@dataclass(frozen=True)
class TextFile:
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def search(self, needle: str) -> list[tuple[int, str]]:
        return [(i, line) for i, line in enumerate(self.read().splitlines(), 1) if needle in line]


def iter_text_files(root: Path, pattern: str = "*.txt") -> Iterator[Path]:
    if not root.is_dir():
        raise NotADirectoryError(root)
    yield from sorted(path for path in root.rglob(pattern) if path.is_file())


def _search_one(task: tuple[Path, str]) -> tuple[Path, list[tuple[int, str]]]:
    path, needle = task
    return path, TextFile(path).search(needle)


def search_files(root: Path, needle: str, pattern: str = "*.txt") -> Iterator[tuple[Path, list[tuple[int, str]]]]:
    logger.debug("Searching {} for {!r}", root, needle)
    tasks = ((path, needle) for path in iter_text_files(root, pattern))
    with Pool(processes=4) as pool:
        for path, matches in pool.imap_unordered(_search_one, tasks):
            if matches:
                yield path, matches
