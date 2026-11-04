from __future__ import annotations

import time
from collections.abc import Callable

from aitextaroo.conversation import Conversation


class CommandRouter:
    PREFIX = "/"

    def __init__(
        self,
        agent_name: str,
        conversation: Conversation,
        start_time: float | None = None,
    ) -> None:
        self._agent_name = agent_name
        self._conversation = conversation
        self._start_time = start_time or time.time()
        self._message_count = 0

        self._commands: dict[str, tuple[str, Callable[[], str]]] = {
            "help": ("List commands", self._cmd_help),
            "new": ("Start a new conversation", self._cmd_new),
            "status": ("Show bridge status", self._cmd_status),
        }

    @property
    def message_count(self) -> int:
        return self._message_count

    def increment_message_count(self) -> None:
        self._message_count += 1

    def is_command(self, text: str) -> bool:
        return text.startswith(self.PREFIX) and len(text) > 1

    def handle(self, text: str) -> str:
        parts = text[len(self.PREFIX) :].strip().split(maxsplit=1)
        name = parts[0].lower() if parts else ""

        entry = self._commands.get(name)
        if entry is None:
            return f"Unknown command: /{name}\nType /help for available commands."

        _, handler = entry
        return handler()

    def _cmd_help(self) -> str:
        lines = ["Available commands:"]
        for name, (description, _) in self._commands.items():
            lines.append(f"  /{name} — {description}")
        return "\n".join(lines)

    def _cmd_new(self) -> str:
        self._conversation.clear()
        session_id = self._conversation.session_id
        if session_id:
            return f"New session started ({session_id}). Fresh start!"
        return "Conversation cleared. Fresh start!"

    def _cmd_status(self) -> str:
        uptime = time.time() - self._start_time
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        elif minutes > 0:
            uptime_str = f"{minutes}m {seconds}s"
        else:
            uptime_str = f"{seconds}s"

        parts = [
            f"Agent: {self._agent_name}",
            f"Uptime: {uptime_str}",
            f"Messages: {self._message_count}",
            f"History: {self._conversation.count} messages",
        ]

        session_id = self._conversation.session_id
        if session_id:
            parts.append(f"Session: {session_id}")
            session_count = self._conversation.session_count()
            parts.append(f"Sessions on disk: {session_count}")

        return "\n".join(parts)
