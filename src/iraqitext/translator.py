import json
import re
from pathlib import Path
from .rules import normalize

BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "dialects" / "dictionary.json", "r", encoding="utf-8") as f:
    dictionary = json.load(f)

_fusha_phrases = sorted(
    [(v, k) for k, v in dictionary.items()],
    key=lambda pair: len(pair[0]),
    reverse=True,
)

_iraqi_phrases = sorted(
    [(normalize(k), v) for k, v in dictionary.items()],
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def _word_replacements(text, phrases):
    for pattern, replacement in phrases:
        regex = re.compile(r"(?<!\S)" + re.escape(pattern) + r"(?!\S)")
        text = regex.sub(replacement, text)
    return text


class IraqiTranslator:
    def to_fusha(self, text: str) -> str:
        return _word_replacements(text, _iraqi_phrases)

    def to_iraqi(self, text: str) -> str:
        return _word_replacements(text, _fusha_phrases)
