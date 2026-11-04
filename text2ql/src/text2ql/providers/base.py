from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        pass

    async def acomplete(self, system_prompt: str, user_prompt: str) -> str:
        return await asyncio.to_thread(self.complete, system_prompt, user_prompt)

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str:
        logger.debug(
            "complete_structured: no structured-output support in %s; falling back to plain complete()",
            type(self).__name__,
        )
        return self.complete(system_prompt, user_prompt)

    async def acomplete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str:
        return await asyncio.to_thread(self.complete_structured, system_prompt, user_prompt, json_schema)
