"""
textkit.py

Single-file text loading, sentence segmentation, token generation,
and embedding utilities.

Optional dependencies:
    pip install numpy tqdm joblib logzero loguru cchardet
    pip install sentence-splitter polyglot

Example:
    from textkit import load_text, sent_tokenizer, encoder

    text = load_text("book.txt")
    sentences = sent_tokenizer(text, lang="en")
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any, NamedTuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LANGUAGES_SUPPORTED_BY_SENTENCE_SPLITTER = frozenset(
    {
        "ca",
        "cs",
        "da",
        "nl",
        "en",
        "fi",
        "fr",
        "de",
        "el",
        "hu",
        "is",
        "it",
        "lv",
        "lt",
        "no",
        "pl",
        "pt",
        "ro",
        "ru",
        "sk",
        "sl",
        "es",
        "sv",
        "tr",
    }
)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class Token(NamedTuple):
    text: str
    label: str
    paragraph: int
    kind: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_language(text: str) -> str:
    """Detect a language using Polyglot, falling back to English."""
    try:
        from polyglot.text import Detector

        return Detector(text).language.code
    except Exception:
        return "en"


def _split_batches(
    values: Iterable[str],
    size: int,
) -> Iterator[list[str]]:
    """Yield lists containing at most size items."""
    if size < 1:
        raise ValueError("batch size must be greater than zero")

    batch: list[str] = []

    for value in values:
        batch.append(value)

        if len(batch) == size:
            yield batch
            batch = []

    if batch:
        yield batch


def _get_cache() -> Any:
    """Create the joblib cache used by sent_tokenizer and list_tokens."""
    from joblib import Memory

    if os.environ.get("JLNOCACHE"):
        return Memory(location=None, verbose=0)

    return Memory(
        location=Path("~/joblib_cache").expanduser(),
        verbose=0,
    )


# ---------------------------------------------------------------------------
# Text loading
# ---------------------------------------------------------------------------

def load_text(filename: str | Path) -> str:
    """
    Load a text file, detect its encoding, normalize full-width spaces,
    and remove empty lines.

    Parameters
    ----------
    filename:
        Path to the input text file.

    Returns
    -------
    str
        Cleaned text with one non-empty input line per output line.
    """
    path = Path(filename)

    if not path.is_file():
        raise FileNotFoundError(
            f"{path.resolve()} does not exist or is not a file"
        )

    try:
        import cchardet

        detected = cchardet.detect(path.read_bytes())
        encoding = detected.get("encoding") or "utf-8"
    except Exception:
        encoding = "utf-8"

    content = path.read_text(encoding=encoding, errors="replace")
    content = content.replace("\u3000", " ")

    return "\n".join(
        line.strip()
        for line in content.splitlines()
        if line.strip()
    )


# ---------------------------------------------------------------------------
# Sentence segmentation
# ---------------------------------------------------------------------------

def seg_text(
    text: str,
    lang: str | None = None,
    qmode: bool = False,
    maxlines: int = 1000,
) -> list[str]:
    """
    Split text into sentences.

    For languages supported by sentence-splitter, each input line is
    processed separately. Polyglot is used as a fallback.
    """
    if not text.strip():
        return []

    lang = lang or _detect_language(text)

    if not qmode and lang in LANGUAGES_SUPPORTED_BY_SENTENCE_SPLITTER:
        from sentence_splitter import split_text_into_sentences

        lines = text.splitlines()
        sentences: list[str] = []

        for line in lines:
            if line.strip():
                sentences.extend(
                    split_text_into_sentences(line, lang)
                )

        return sentences

    try:
        from polyglot.text import Text

        return [
            sentence.string
            for sentence in Text(text, lang).sentences
        ]
    except Exception:
        # A conservative fallback if Polyglot is unavailable or fails.
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?。！？])\s+", text)
            if sentence.strip()
        ]


def _sent_tokenizer(
    text: str | Sequence[str],
    lang: str | None = None,
    debug: bool = False,
) -> list[str]:
    """
    Split a string or sequence of strings into sentences.
    """
    del debug  # Kept for API compatibility.

    items = [text] if isinstance(text, str) else list(text)

    if not items:
        return []

    lang = lang or _detect_language(" ".join(items))

    sentences: list[str] = []

    for item in items:
        sentences.extend(seg_text(item, lang=lang))

    return sentences


# Create the cached public tokenizer while keeping the uncached function
# available for callers that need it.
sent_tokenizer = _get_cache().cache(
    _sent_tokenizer,
    ignore=["debug"],
)


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def gen_tokens(
    text: str | Sequence[str],
    label: str = "",
    lang: str | None = None,
    gen_para: bool = False,
    gen_sent: bool = True,
    gen_phrase: bool = False,
) -> Iterator[Token]:
    """
    Generate paragraph and/or sentence tokens in input order.

    Paragraph numbering is one-based. Sentence tokens use the paragraph
    number containing each sentence.
    """
    if isinstance(text, str):
        paragraphs = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]
    else:
        paragraphs = [
            paragraph.strip()
            for paragraph in text
            if paragraph.strip()
        ]

    if not paragraphs:
        return

    lang = lang or _detect_language(" ".join(paragraphs))

    if gen_para:
        for index, paragraph in enumerate(paragraphs, start=1):
            yield Token(paragraph, label, index, "para")

    if gen_sent:
        for index, paragraph in enumerate(paragraphs, start=1):
            for sentence in _sent_tokenizer(paragraph, lang):
                yield Token(sentence, label, index, "sent")

    if gen_phrase:
        raise NotImplementedError(
            "Phrase tokenization is not implemented. "
            "Install and integrate a phrase tokenizer such as benepar."
        )


list_tokens = _get_cache().cache(gen_tokens)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def encoder(
    data: Iterable[str],
    embed: Callable[[list[str]], Any] | None = None,
    b_size: int = 100,
) -> "np.ndarray":
    """
    Embed text in batches