import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class Bookmark:
    chapter_index: int
    line_offset: int
    percentage: float
    last_read: str
    title: str

    @classmethod
    def create(
        cls,
        chapter_index: int,
        line_offset: int,
        percentage: float,
        title: str,
    ) -> "Bookmark":
        return cls(
            chapter_index=chapter_index,
            line_offset=line_offset,
            percentage=percentage,
            last_read=datetime.now(timezone.utc).isoformat(),
            title=title,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Bookmark":
        return cls(
            chapter_index=int(data.get("chapter_index", 0)),
            line_offset=int(data.get("line_offset", 0)),
            percentage=float(data.get("percentage", 0.0)),
            last_read=str(data.get("last_read", "")),
            title=str(data.get("title", "")),
        )


class BookmarkManager:
    def __init__(self, bookmark_file: Path | None = None) -> None:
        if bookmark_file is None:
            self.bookmark_file = Path.home() / ".epub2text" / "bookmarks.json"
        else:
            self.bookmark_file = bookmark_file
        self._bookmarks: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        self._bookmarks = {}
        if not self.bookmark_file.exists():
            return

        data = self._read_bookmarks_file(self.bookmark_file)
        if data is not None:
            self._bookmarks = data.get("bookmarks", {})
            return

        backup_path = self._backup_path()
        if backup_path.exists():
            backup_data = self._read_bookmarks_file(backup_path)
            if backup_data is not None:
                self._bookmarks = backup_data.get("bookmarks", {})
                logger.warning("Recovered bookmarks from backup: %s", backup_path)

    def _save(self) -> None:
        self.bookmark_file.parent.mkdir(parents=True, exist_ok=True)

        data = {"bookmarks": self._bookmarks}
        backup_path = self._backup_path()
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.bookmark_file.parent,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp_path = Path(tmp.name)
                json.dump(data, tmp, indent=2, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())

            if self.bookmark_file.exists():
                self.bookmark_file.replace(backup_path)
            tmp_path.replace(self.bookmark_file)
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _backup_path(self) -> Path:
        return self.bookmark_file.with_suffix(self.bookmark_file.suffix + ".bak")

    def _read_bookmarks_file(self, path: Path) -> dict[str, Any] | None:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return cast(dict[str, Any], data)
            logger.warning("Unexpected bookmark data structure in %s", path)
            return None
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load bookmarks from %s: %s", path, exc)
            return None

    def _normalize_path(self, epub_path: str) -> str:
        return str(Path(epub_path).resolve())

    def save(self, epub_path: str, bookmark: Bookmark) -> None:
        key = self._normalize_path(epub_path)
        self._bookmarks[key] = asdict(bookmark)
        self._save()

    def load(self, epub_path: str) -> Bookmark | None:
        key = self._normalize_path(epub_path)
        data = self._bookmarks.get(key)
        if data is None:
            return None
        return Bookmark.from_dict(data)

    def delete(self, epub_path: str) -> bool:
        key = self._normalize_path(epub_path)
        if key in self._bookmarks:
            del self._bookmarks[key]
            self._save()
            return True
        return False

    def list_all(self) -> dict[str, Bookmark]:
        return {
            path: Bookmark.from_dict(data) for path, data in self._bookmarks.items()
        }
