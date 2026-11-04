from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import IO, Self

import portalocker


def _diag_payload(tag: str) -> str:
    return json.dumps({
        "pid": os.getpid(),
        "acquired_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "tag": tag,
    })


class LockHeld(RuntimeError):
    def __init__(self, path: Path, diagnostic: str | None = None) -> None:
        suffix = f" (held by {diagnostic})" if diagnostic else ""
        super().__init__(f"Lock {path} is held by another process{suffix}.")
        self.path = path
        self.diagnostic = diagnostic


class FileLock:
    def __init__(self, path: Path, tag: str = "") -> None:
        self.path = path
        self.tag = tag
        self._fh: IO[str] | None = None

    def __enter__(self) -> Self:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fh = open(self.path, "a+", encoding="utf-8")
        except PermissionError as exc:
            raise LockHeld(self.path, read_holder(self.path)) from exc
        try:
            portalocker.lock(fh, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except (portalocker.LockException, PermissionError) as exc:
            try:
                diag = _read_holder(fh)
            except OSError:
                diag = None
            fh.close()
            raise LockHeld(self.path, diag) from exc
        fh.seek(0)
        fh.truncate()
        fh.write(_diag_payload(self.tag))
        fh.flush()
        self._fh = fh

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            portalocker.unlock(self._fh)
        finally:
            self._fh.close()
            self._fh = None


def try_acquire(path: Path, tag: str = "") -> FileLock | None:
    lock = FileLock(path, tag=tag)
    try:
        lock.acquire()
    except LockHeld:
        return None
    return lock


def read_holder(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return _read_holder(fh)
    except OSError:
        return None


def _read_holder(fh: IO[str]) -> str | None:
    fh.seek(0)
    body = fh.read().strip()
    if not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body[:200]
    pid = data.get("pid")
    tag = data.get("tag") or "?"
    acquired = data.get("acquired_at", "?")
    return f"pid={pid} tag={tag} since={acquired}"
