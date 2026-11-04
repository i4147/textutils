from dotenv import load_dotenv
import openai
import os
import asyncio
from typing import Optional

OPENAI_API_KEY_NAME = "OPENAI_API_KEY"
LINTING_MODEL = "gpt-5-mini"


class AILinter:
    def __init__(self, api_key: Optional[str] = None):
        if not openai.api_key:
            if api_key:
                key = api_key
            else:
                load_dotenv()
                key = os.getenv(OPENAI_API_KEY_NAME)
            if not key:
                raise ValueError(f'No api key provided. No value found in env for key "{OPENAI_API_KEY_NAME}"')
            openai.api_key = key

    def remove_backticks(self, text: str) -> str:
        stripped = text.strip()
        start = 3 if stripped.startswith("```") else 0
        end = -3 if stripped.endswith("```") else len(stripped)

        return f"{stripped[start:end]}\n\n"

    def get_message(self, role: str, prompt: str) -> dict:
        if role != "system" and role != "user":
            raise ValueError("role must be either 'system' or 'user'")
        return {
            "role": role,
            "content": prompt,
        }

    async def make_request(self, model: str, messages: list) -> str:
        client = openai.AsyncOpenAI()
        completion = await client.chat.completions.create(model=model, messages=messages)
        obj = completion.choices[0]
        res = obj.message.content
        return self.remove_backticks(res)

    async def lint_text(self, text: str, linting_prompt: str) -> str:
        return await self.make_request(
            LINTING_MODEL,
            [
                self.get_message("system", linting_prompt),
                self.get_message("user", f"Please clean up the following text: \n\n{text}"),
            ],
        )

    async def batch_lint_texts(
        self,
        texts: list[str],
        linting_prompt: str,
    ) -> list[str]:
        res = [self.lint_text(text, linting_prompt) for text in texts]
        return await asyncio.gather(*res)
