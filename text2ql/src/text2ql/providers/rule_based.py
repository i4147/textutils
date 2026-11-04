from __future__ import annotations

from .base import LLMProvider


class RuleBasedProvider(LLMProvider):
    def complete(self, _system_prompt: str, user_prompt: str) -> str:
        return user_prompt
