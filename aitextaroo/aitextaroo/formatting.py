from __future__ import annotations

import re


def format_for_sms(text: str) -> str:
    text = re.sub(r"```[a-z]*\n?", "", text)

    text = re.sub(r"`(.+?)`", r"\1", text)

    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)

    text = re.sub(r"\*(.+?)\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text, flags=re.DOTALL)

    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    text = re.sub(r"^\s*[*+]\s+", "- ", text, flags=re.MULTILINE)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
