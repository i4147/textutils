from __future__ import annotations

import enum
import threading
from dataclasses import dataclass, field
from typing import Any


class ServerState(enum.StrEnum):
    INITIAL_INDEX = "initial_index"
    WAITING_ON_INDEXER = "waiting_on_indexer"
    INDEXING_REINDEX = "indexing_reindex"
    STALE_CHECKING = "stale_checking"
    READY = "ready"
    ERROR = "error"


_TRANSIENT_STATES: frozenset[ServerState] = frozenset({
    ServerState.INITIAL_INDEX,
    ServerState.WAITING_ON_INDEXER,
    ServerState.INDEXING_REINDEX,
    ServerState.STALE_CHECKING,
})


@dataclass
class ServerContext:
    state: ServerState = ServerState.INITIAL_INDEX
    files_indexed: int = 0
    files_total: int = 0
    error_message: str | None = None
    is_reader_only: bool = False
    promotion_done: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set_state(
        self,
        new_state: ServerState,
        *,
        error_message: str | None = None,
    ) -> None:
        with self._lock:
            self.state = new_state
            self.error_message = error_message

    def update_progress(self, indexed: int, total: int) -> None:
        with self._lock:
            self.files_indexed = indexed
            self.files_total = total

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": self.state.value,
                "files_indexed": self.files_indexed,
                "files_total": self.files_total,
                "error_message": self.error_message,
            }

    def is_ready(self) -> bool:
        with self._lock:
            return self.state is ServerState.READY

    def is_transient(self) -> bool:
        with self._lock:
            return self.state in _TRANSIENT_STATES

    def busy_message(self) -> str:
        snap = self.snapshot()
        state = snap["state"]
        indexed, total = snap["files_indexed"], snap["files_total"]
        if state == ServerState.INITIAL_INDEX.value:
            base = "symtext is performing initial indexing of this project"
        elif state == ServerState.INDEXING_REINDEX.value:
            base = "symtext is rebuilding the index (schema upgrade)"
        elif state == ServerState.STALE_CHECKING.value:
            base = "symtext is checking for files changed since the last session"
        elif state == ServerState.WAITING_ON_INDEXER.value:
            base = "symtext is waiting for another process to finish indexing this project"
        else:
            base = f"symtext is in state {state}"
        if total:
            base += f" ({indexed}/{total} files)"
        return base + ". Please retry shortly."
