from __future__ import annotations

import json
import logging
import os
import uuid
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Message:
    role: str
    text: str
    ts: float = 0.0

    _VALID_ROLES: ClassVar[frozenset[str]] = frozenset({"user", "assistant"})

    def to_jsonl(self) -> str:
        return json.dumps({"role": self.role, "text": self.text, "ts": self.ts})

    @classmethod
    def from_dict(cls, data: dict) -> Message | None:
        role = data.get("role", "")
        text = data.get("text", "")
        if role not in cls._VALID_ROLES or not isinstance(text, str):
            return None
        return cls(role=role, text=text, ts=data.get("ts", 0.0))


class Conversation:
    def __init__(
        self,
        max_messages: int = 20,
        sessions_dir: Path | None = None,
        session_id: str | None = None,
    ) -> None:
        self._messages: deque[Message] = deque(maxlen=max_messages)
        self._max_messages = max_messages
        self._sessions_dir = sessions_dir
        self._session_id = session_id

        if sessions_dir is not None:
            sessions_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(sessions_dir, 0o700)
            if session_id is None:
                self._session_id = _generate_session_id()
            _touch_private(self._session_path)

    @classmethod
    def load_latest(
        cls,
        sessions_dir: Path,
        max_messages: int = 20,
        retention_days: int = 90,
    ) -> Conversation:
        sessions_dir.mkdir(parents=True, exist_ok=True)

        if retention_days > 0:
            _cleanup_old_sessions(sessions_dir, retention_days)

        session_files = sorted(
            [f for f in sessions_dir.glob("*.jsonl") if f.exists()],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        if not session_files:
            conv = cls(max_messages=max_messages, sessions_dir=sessions_dir)
            logger.info("No existing sessions. Created new session %s", conv.session_id)
            return conv

        latest = session_files[0]
        session_id = latest.stem

        conv = cls(
            max_messages=max_messages,
            sessions_dir=sessions_dir,
            session_id=session_id,
        )
        conv._load_from_file(latest)
        logger.info(
            "Loaded session %s (%d messages)",
            session_id,
            conv.count,
        )
        return conv

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def _session_path(self) -> Path:
        if self._sessions_dir is None:
            raise RuntimeError("Cannot access session path in in-memory mode")
        return self._sessions_dir / f"{self._session_id}.jsonl"

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    @property
    def count(self) -> int:
        return len(self._messages)

    @property
    def is_empty(self) -> bool:
        return len(self._messages) == 0

    def add_user_message(self, text: str) -> None:
        self._add(Message(role="user", text=text, ts=_now()))

    def add_assistant_message(self, text: str) -> None:
        self._add(Message(role="assistant", text=text, ts=_now()))

    def new_session(self) -> str | None:
        self._messages.clear()

        if self._sessions_dir is None:
            return None

        new_id = _generate_session_id()
        self._session_id = new_id
        _touch_private(self._session_path)
        logger.info("New session %s", new_id)
        return new_id

    def clear(self) -> None:
        if self._sessions_dir is not None:
            self.new_session()
        else:
            self._messages.clear()

    def session_count(self) -> int:
        if self._sessions_dir is None:
            return 0
        return len(list(self._sessions_dir.glob("*.jsonl")))

    def format_as_context(self) -> str:
        if not self._messages:
            return ""

        lines = ["[Conversation history]"]
        for msg in self._messages:
            label = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{label}: {msg.text}")

        return "\n".join(lines)

    def _add(self, message: Message) -> None:
        self._messages.append(message)
        if self._sessions_dir is not None:
            self._append_to_file(message)

    def _append_to_file(self, message: Message) -> None:
        line = message.to_jsonl() + "\n"
        path = self._session_path

        try:
            tmp_path = path.with_suffix(".tmp")
            tmp_path.write_text(line, encoding="utf-8")

            written = tmp_path.read_text(encoding="utf-8").strip()
            json.loads(written)

            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())

            tmp_path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Failed to write to session file %s", path)
        except json.JSONDecodeError:
            logger.error("Corrupt write detected, discarding line for %s", path)
            tmp_path.unlink(missing_ok=True)

    def _load_from_file(self, path: Path) -> None:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            logger.exception("Failed to read session file %s", path)
            return

        recent_lines = lines[-self._max_messages :] if lines else []
        file_offset = len(lines) - len(recent_lines)

        for idx, line in enumerate(recent_lines):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Skipping corrupt line %d in %s", file_offset + idx + 1, path.name)
                continue

            msg = Message.from_dict(data)
            if msg is None:
                logger.warning("Skipping invalid message at line %d in %s", file_offset + idx + 1, path.name)
                continue

            self._messages.append(msg)


def _touch_private(path: Path) -> None:
    with open(path, "a"):
        pass
    os.chmod(path, 0o600)


def _generate_session_id() -> str:
    return uuid.uuid4().hex[:8]


def _now() -> float:
    import time

    return time.time()


def _cleanup_old_sessions(sessions_dir: Path, retention_days: int) -> None:
    import time

    cutoff = time.time() - (retention_days * 86400)
    for f in sessions_dir.glob("*.jsonl"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                logger.info("Cleaned up old session: %s", f.name)
        except OSError:
            logger.warning("Failed to clean up %s", f.name)
