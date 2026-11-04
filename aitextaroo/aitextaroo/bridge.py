from __future__ import annotations

import logging
from pathlib import Path

from aitextaroo.agents import Agent
from aitextaroo.client import TextarooClient
from aitextaroo.commands import CommandRouter
from aitextaroo.conversation import Conversation
from aitextaroo.formatting import format_for_sms
from aitextaroo.models import InboundMessage

logger = logging.getLogger(__name__)

MAX_SMS_LENGTH = 1600


class Bridge:
    def __init__(
        self,
        client: TextarooClient,
        agent: Agent,
        max_history: int = 20,
        sessions_dir: Path | None = None,
    ) -> None:
        self._client = client
        self._agent = agent

        if sessions_dir is not None:
            self._conversation = Conversation.load_latest(
                sessions_dir,
                max_messages=max_history,
            )
            logger.info(
                "Session %s loaded (%d messages)",
                self._conversation.session_id,
                self._conversation.count,
            )
        else:
            self._conversation = Conversation(max_messages=max_history)

        self._commands = CommandRouter(
            agent_name=agent.name,
            conversation=self._conversation,
        )

    async def run(self) -> None:
        try:
            async for message in self._client.listen():
                await self._handle(message)
        finally:
            await self._agent.close()
            await self._client.close()

    async def _handle(self, message: InboundMessage) -> None:
        text = message.text.strip()

        if self._commands.is_command(text):
            response = self._commands.handle(text)
            await self._send(response)
            return

        await self._handle_conversation(message.id, text)

    async def _handle_conversation(self, message_id: str, text: str) -> None:
        logger.info("Inbound SMS [%s]: %s", message_id, text[:50])

        prompt = self._build_prompt(text)

        try:
            response = await self._agent.ask(prompt)
        except TimeoutError:
            logger.error("Agent timed out on message %s", message_id)
            await self._send("Sorry, I took too long to respond. Try again?")
            return
        except Exception:
            logger.exception("Agent error on message %s", message_id)
            await self._send("Sorry, something went wrong. Try again?")
            return

        if not response:
            logger.warning("Agent returned empty response for %s", message_id)
            return

        self._conversation.add_user_message(text)
        self._conversation.add_assistant_message(response)
        self._commands.increment_message_count()

        formatted = format_for_sms(response)
        if len(formatted) > MAX_SMS_LENGTH:
            formatted = formatted[: MAX_SMS_LENGTH - 3] + "..."
            logger.warning("Response truncated to %d chars", MAX_SMS_LENGTH)

        await self._send(formatted)
        logger.info("Reply sent for %s", message_id)

    def _build_prompt(self, text: str) -> str:
        parts: list[str] = []

        system = self._agent.system_prompt
        if system:
            parts.append(f"[System]\n{system}")

        context = self._conversation.format_as_context()
        if context:
            parts.append(context)

        parts.append(f"[New message]\nUser: {text}")

        return "\n\n".join(parts)

    async def _send(self, text: str) -> None:
        try:
            await self._client.send(text)
        except Exception:
            logger.exception("Failed to send reply")
