from __future__ import annotations

import asyncio
import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120


class Agent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def system_prompt(self) -> str:
        return ""

    @abstractmethod
    async def ask(self, text: str) -> str:
        pass

    async def close(self) -> None:
        pass


@dataclass(frozen=True, slots=True)
class CliAgentConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    system_prompt: str = ""
    timeout: float = DEFAULT_TIMEOUT


class CliAgent(Agent):
    def __init__(self, config: CliAgentConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def system_prompt(self) -> str:
        return self._config.system_prompt

    async def ask(self, text: str) -> str:
        cmd = [self._config.command, *self._config.args, text]

        logger.debug("Running: %s %s '%s...'", cmd[0], " ".join(cmd[1:-1]), text[:40])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._config.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        if process.returncode != 0:
            error_text = stderr.decode(errors="replace")[:200]
            logger.warning(
                "Agent %s exited with code %d: %s",
                self._config.name,
                process.returncode,
                error_text,
            )

        return stdout.decode(errors="replace").strip()


BUILTIN_AGENTS: dict[str, CliAgentConfig] = {
    "claude": CliAgentConfig(
        name="Claude Code",
        command="claude",
        args=["-p"],
        system_prompt=(
            "You are receiving SMS text messages from a user. "
            "Respond concisely — these are text messages with a 1600 character limit."
        ),
    ),
    "hermes": CliAgentConfig(
        name="Hermes",
        command="hermes",
        args=["--pipe"],
        system_prompt=(
            "You are receiving SMS text messages from a user via AI Text-a-roo. "
            "Respond conversationally. Keep responses concise — they're text messages."
        ),
    ),
    "openclaw": CliAgentConfig(
        name="OpenClaw",
        command="openclaw",
        args=["--pipe"],
        system_prompt="You are receiving SMS text messages. Respond concisely.",
    ),
    "nanoclaw": CliAgentConfig(
        name="NanoClaw",
        command="nanoclaw",
        args=["--pipe"],
        system_prompt="You are receiving SMS text messages. Respond concisely.",
    ),
}


def detect_agents() -> list[str]:
    found = []
    for name, config in BUILTIN_AGENTS.items():
        if shutil.which(config.command):
            found.append(name)
            logger.debug("Detected agent: %s (%s)", config.name, config.command)
    return found


def create_agent(name: str) -> CliAgent:
    config = BUILTIN_AGENTS.get(name)
    if config is None:
        available = ", ".join(BUILTIN_AGENTS.keys())
        raise ValueError(f"Unknown agent: {name!r}. Available: {available}")
    return CliAgent(config)
